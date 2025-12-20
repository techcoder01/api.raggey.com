from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from decimal import Decimal

from .models import Purchase, Item, DeliverySettings
from Sizes.models import Sizes
from .serializers import (
    PurchaseSerializer,
    PurchaseCreateSerializer,
    PurchaseListSerializer,
    PurchaseStatusUpdateSerializer,
    ItemSerializer
)
from .utils import (
    check_stock_availability,
    deduct_inventory,
    restore_inventory,
    calculate_basket_total
)


# ================ USER-SIDE VIEWS ================

class CreateOrderAPIView(APIView):
    """
    POST: Create order directly from cart items (cart-based, not basket)
    Endpoint: /purchase/create-order/
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            user = request.user

            # Extract order data
            full_name = request.data.get('full_name', '')
            phone_number = request.data.get('phone_number', '')
            email = request.data.get('email', user.email)
            address_name = request.data.get('address_name', '')
            area = request.data.get('Area', '')
            block = request.data.get('block', '')
            street = request.data.get('street', '')
            house = request.data.get('house', '')
            apartment = request.data.get('apartment', '')
            floor = request.data.get('floor', '')
            latitude = request.data.get('latitude', '')
            longitude = request.data.get('longitude', '')
            payment_option = request.data.get('payment_option', 'Cash')
            is_pick_up = request.data.get('is_pick_up', False)
            delivery_fee = Decimal(str(request.data.get('delivery_fee', '0.000')))
            cart_items = request.data.get('cart_items', [])

            if not cart_items:
                return Response({
                    'error': 'Empty cart',
                    'message': 'Cart is empty'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Calculate total price from cart items
            total_price = Decimal('0.000')
            for item in cart_items:
                price = Decimal(str(item.get('price', 0)))
                quantity = int(item.get('quantity', 1))
                total_price += price * quantity

            # Add delivery fee
            total_price += delivery_fee

            # Create Purchase (Order)
            purchase = Purchase.objects.create(
                user=user,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                address_name=address_name,
                Area=area,
                block=block,
                street=street,
                house=house,
                apartment=apartment,
                floor=floor,
                latitude=latitude,
                longitude=longitude,
                payment_option=payment_option,
                is_pick_up=is_pick_up,
                is_cash=True,  # Direct order is always cash for now
                total_price=total_price,
                delivery_fee=delivery_fee,
                status='Pending'
            )

            # Create order items
            for idx, cart_item in enumerate(cart_items, start=1):
                # Generate product code: INV-XXXXX-ITEM-1, INV-XXXXX-ITEM-2, etc.
                product_code = f"{purchase.invoice_number}-ITEM-{idx}"

                # Generate product ID: order ID + index (unique identifier)
                product_id = int(f"{purchase.id}{idx:03d}")  # e.g., 1001, 1002 for order ID 1

                product_name = cart_item.get('name', 'Custom Design')
                category = cart_item.get('category', 'Custom Design')
                unit_price = Decimal(str(cart_item.get('price', 0)))
                quantity = int(cart_item.get('quantity', 1))
                net_amount = unit_price * quantity
                discount_percentage = cart_item.get('discount_percentage')
                product_size = cart_item.get('size', '')
                image_url = cart_item.get('imageUrl', '')
                design_details = cart_item.get('design_details')
                size_details = cart_item.get('size_details')

                # Check if custom measurements exist and create Sizes entry
                selected_size = None
                if size_details and size_details.get('measurement_type') == 'custom':
                    # Helper function to safely convert measurement to int
                    def safe_int(value):
                        if not value:
                            return 0
                        try:
                            # Convert to string, strip whitespace and any brackets
                            cleaned = str(value).strip().strip('[]{}()')
                            return int(float(cleaned)) if cleaned else 0
                        except (ValueError, TypeError):
                            return 0

                    # Create Sizes entry for custom measurements
                    selected_size = Sizes.objects.create(
                        user=user,
                        size_name=f"{product_name} - Order {purchase.invoice_number}",
                        front_hight=safe_int(size_details.get('custom_front_height')),
                        back_hight=safe_int(size_details.get('custom_back_height')),
                        around_neck=safe_int(size_details.get('custom_neck')),
                        around_legs=safe_int(size_details.get('custom_around_legs')),
                        full_chest=safe_int(size_details.get('custom_full_chest')),
                        half_chest=safe_int(size_details.get('custom_half_chest')),
                        full_belly=safe_int(size_details.get('custom_full_belly')),
                        half_belly=safe_int(size_details.get('custom_half_belly')),
                        neck_to_center_belly=safe_int(size_details.get('custom_neck_to_belly')),
                        neck_to_chest=safe_int(size_details.get('custom_neck_to_pocket')),
                        shoulders_width=safe_int(size_details.get('custom_shoulder_width')),
                        arm_tall=safe_int(size_details.get('custom_arm_tall')),
                        arm_width_one=safe_int(size_details.get('custom_arm_width_1')),
                        arm_width_two=safe_int(size_details.get('custom_arm_width_2')),
                        arm_width_three=safe_int(size_details.get('custom_arm_width_3')),
                        arm_width_four=safe_int(size_details.get('custom_arm_width_4')),
                    )

                # Create Item with JSON fields AND Sizes table entry
                Item.objects.create(
                    invoice=purchase,
                    product_code=product_code,
                    product_id=product_id,
                    selected_size=selected_size,  # Link to Sizes table
                    product_name=product_name,
                    category=category,
                    unit_price=unit_price,
                    net_amount=net_amount,
                    discount=Decimal('0.000'),
                    discount_percentage=discount_percentage,
                    quantity=quantity,
                    product_size=product_size,
                    cover=image_url,
                    design_details=design_details,  # Store design as JSON
                    size_details=size_details,  # Store measurements as JSON
                )

            # Return created order
            response_serializer = PurchaseSerializer(purchase)
            return Response({
                'message': 'Order created successfully',
                'order': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': 'Order creation failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderHistoryAPIView(APIView):
    """
    GET: Get user's order history
    Endpoint: /purchase/orders/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            orders = Purchase.objects.filter(user=user).order_by('-timestamp')
            serializer = PurchaseListSerializer(orders, many=True)
            return Response({
                'orders': serializer.data,
                'count': orders.count()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Failed to fetch orders',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderDetailAPIView(APIView):
    """
    GET: Get order details by ID
    Endpoint: /purchase/order/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = request.user
            try:
                order = Purchase.objects.get(id=pk, user=user)
            except Purchase.DoesNotExist:
                return Response({
                    'error': 'Order not found',
                    'message': 'This order does not exist or you do not have permission to view it'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = PurchaseSerializer(order)
            return Response({
                'order': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch order',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelOrderAPIView(APIView):
    """
    POST: Cancel an order (only if status is Pending)
    Endpoint: /purchase/order/<id>/cancel/
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            user = request.user

            # Get order
            try:
                order = Purchase.objects.get(id=pk, user=user)
            except Purchase.DoesNotExist:
                return Response({
                    'error': 'Order not found',
                    'message': 'This order does not exist or you do not have permission to cancel it'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if order can be cancelled
            if order.status not in ['Pending', 'Processing']:
                return Response({
                    'error': 'Cannot cancel order',
                    'message': f'Orders with status "{order.status}" cannot be cancelled'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Restore inventory
            for item in order.items.all():
                if item.user_design:
                    restore_inventory(item.user_design, order.invoice_number)

            # Update order status
            order.status = 'Cancelled'
            order.save()

            serializer = PurchaseSerializer(order)
            return Response({
                'message': 'Order cancelled successfully',
                'order': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to cancel order',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliverySettingsAPIView(APIView):
    """
    GET: Get current delivery settings (days and cost)
    Endpoint: /purchase/delivery-settings/
    """
    permission_classes = []  # Public endpoint

    def get(self, request):
        try:
            # Get active delivery settings
            settings = DeliverySettings.objects.filter(is_active=True).first()

            if not settings:
                # Return default values if no settings exist
                return Response({
                    'delivery_days': 5,
                    'delivery_cost': '2.000'
                }, status=status.HTTP_200_OK)

            return Response({
                'delivery_days': settings.delivery_days,
                'delivery_cost': str(settings.delivery_cost)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch delivery settings',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================ ADMIN-SIDE VIEWS ================

class AdminOrderListAPIView(APIView):
    """
    GET: Get all orders (admin)
    Endpoint: /purchase/admin/orders/
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Get query parameters for filtering
            status_filter = request.GET.get('status', None)

            orders = Purchase.objects.all().order_by('-timestamp')

            if status_filter:
                orders = orders.filter(status=status_filter)

            serializer = PurchaseListSerializer(orders, many=True)
            return Response({
                'orders': serializer.data,
                'count': orders.count()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch orders',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminOrderDetailAPIView(APIView):
    """
    GET: Get order details (admin)
    Endpoint: /purchase/admin/order/<id>/
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            try:
                order = Purchase.objects.get(id=pk)
            except Purchase.DoesNotExist:
                return Response({
                    'error': 'Order not found',
                    'message': 'This order does not exist'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = PurchaseSerializer(order)
            return Response({
                'order': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch order',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminUpdateOrderStatusAPIView(APIView):
    """
    PUT: Update order status (admin)
    Endpoint: /purchase/admin/order/<id>/status/
    """
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            try:
                order = Purchase.objects.get(id=pk)
            except Purchase.DoesNotExist:
                return Response({
                    'error': 'Order not found',
                    'message': 'This order does not exist'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = PurchaseStatusUpdateSerializer(order, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()

            response_serializer = PurchaseSerializer(order)
            return Response({
                'message': 'Order status updated successfully',
                'order': response_serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to update order status',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminCancelOrderAPIView(APIView):
    """
    POST: Cancel an order and restore inventory (admin)
    Endpoint: /purchase/admin/order/<id>/cancel/
    """
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, pk):
        try:
            # Get order
            try:
                order = Purchase.objects.get(id=pk)
            except Purchase.DoesNotExist:
                return Response({
                    'error': 'Order not found',
                    'message': 'This order does not exist'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if order is already completed
            if order.status == 'Complete':
                return Response({
                    'error': 'Cannot cancel order',
                    'message': 'Completed orders cannot be cancelled'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if order is already cancelled
            if order.status == 'Cancelled':
                return Response({
                    'error': 'Order already cancelled',
                    'message': 'This order is already cancelled'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Restore inventory
            for item in order.items.all():
                if item.user_design:
                    restore_inventory(item.user_design, order.invoice_number)

            # Update order status
            order.status = 'Cancelled'
            order.save()

            serializer = PurchaseSerializer(order)
            return Response({
                'message': 'Order cancelled successfully and inventory restored',
                'order': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to cancel order',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
