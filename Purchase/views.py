from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from decimal import Decimal

from .models import Purchase, Item, DeliverySettings, AboutUs, TermsAndConditions
from Sizes.models import Sizes
from Coupon.models import Coupon, CouponUsage
from Design.models import (
    UserDesign,
    HomePageSelectionCategory,
    FabricColor,
    GholaType,
    SleevesType,
    PocketType,
    ButtonType,

    BodyType,
    InventoryTransaction
)
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
from .notification_utils import send_order_status_notification, initialize_firebase


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

            # Extract coupon data
            coupon_code = request.data.get('coupon_code', None)
            discount_amount = Decimal(str(request.data.get('discount_amount', '0.000')))

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

            # Try to find matching address from user's saved addresses
            from User.models import Address
            selected_address = None
            if area:  # Only search if we have address data
                selected_address = Address.objects.filter(
                    user=user,
                    area=area,
                    block=block,
                    street=street,
                    building=house
                ).first()

                if selected_address:
                    print(f"✅ Found matching saved address: {selected_address}")
                else:
                    print(f"ℹ️ No matching saved address found for area={area}, block={block}, street={street}")

            # Create Purchase (Order)
            purchase = Purchase.objects.create(
                user=user,
                selected_address=selected_address,  # Link to saved address if found
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
                coupon_code=coupon_code,
                discount_amount=discount_amount,
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

                # Add fabric_type_id to design_details if design_color_id exists
                if design_details and design_details.get('design_color_id'):
                    try:
                        fabric_color = FabricColor.objects.get(id=design_details['design_color_id'])
                        design_details['design_fabric_type_id'] = fabric_color.fabric_type.id
                    except (FabricColor.DoesNotExist, AttributeError):
                        pass  # If fabric color not found or has no fabric type, skip

                # NOTE: Sizes and UserDesign entries are created via BulkSaveCartData API (from cart screen)
                # Order creation only stores data in JSON fields (design_details, size_details)
                print(f"📦 Order Item: {product_name} - Storing in JSON only (no UserDesign/Sizes tables)")

                # Create Item with JSON fields only (no separate table entries)
                Item.objects.create(
                    invoice=purchase,
                    product_code=product_code,
                    product_id=product_id,
                    user_design=None,  # Not creating UserDesign during order (done via BulkSaveCartData)
                    selected_size=None,  # Not creating Sizes during order (done via BulkSaveCartData)
                    product_name=product_name,
                    category=category,
                    unit_price=unit_price,
                    net_amount=net_amount,
                    discount=Decimal('0.000'),
                    discount_percentage=discount_percentage,
                    quantity=quantity,
                    product_size=product_size,
                    cover=image_url,
                    design_details=design_details,  # All design data stored as JSON
                    size_details=size_details,  # All measurement data stored as JSON
                )

                # Create InventoryTransaction to deduct fabric stock
                if design_details and design_details.get('design_color_id'):
                    try:
                        with transaction.atomic():
                            fabric_color_id = design_details.get('design_color_id')
                            fabric_color = FabricColor.objects.filter(id=fabric_color_id).first()

                            if fabric_color:
                                # Record current quantity
                                quantity_before = fabric_color.quantity

                                # Deduct 1 unit of fabric per order item
                                quantity_change = -1 * quantity  # Negative for deduction
                                fabric_color.quantity += quantity_change
                                fabric_color.save()

                                # Create transaction record
                                InventoryTransaction.objects.create(
                                    fabric_color=fabric_color,
                                    transaction_type='ORDER',
                                    quantity_change=quantity_change,
                                    quantity_before=quantity_before,
                                    quantity_after=fabric_color.quantity,
                                    reference_order=purchase.invoice_number,
                                    notes=f"Order placed: {product_name}",
                                    created_by=user
                                )
                                print(f"📦 Inventory: Deducted {abs(quantity_change)} unit(s) of {fabric_color.color_name_eng} (Stock: {quantity_before} → {fabric_color.quantity})")
                            else:
                                print(f"⚠️ Warning: Fabric color ID {fabric_color_id} not found")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not create inventory transaction: {e}")
                        # Don't fail order if inventory tracking fails

            # Create CouponUsage entry if coupon was applied
            if purchase.coupon_code and purchase.discount_amount > 0:
                try:
                    with transaction.atomic():
                        coupon = Coupon.objects.filter(code=purchase.coupon_code).first()
                        if coupon:
                            CouponUsage.objects.create(
                                coupon=coupon,
                                user_id=str(user.id),
                                order_id=purchase.invoice_number,
                                discount_amount=purchase.discount_amount,
                                order_amount=purchase.total_price + purchase.discount_amount  # Total before discount
                            )
                            print(f"🎫 CouponUsage created: {purchase.coupon_code} - Discount: {purchase.discount_amount} KWD")
                        else:
                            print(f"⚠️ Warning: Coupon '{purchase.coupon_code}' not found in database")
                except Exception as e:
                    print(f"⚠️ Warning: Could not create coupon usage: {e}")
                    # Don't fail order if coupon tracking fails

            # Send "Order Pending" notification
            try:
                # Get user's FCM token from profile
                user_profile = getattr(user, 'profile', None)
                if user_profile and user_profile.fcm_token:
                    send_order_status_notification(
                        user_fcm_token=user_profile.fcm_token,
                        order=purchase,
                        new_status='Pending'
                    )
                    print(f"🔔 Order Pending notification sent to user {user.id}")
                else:
                    print(f"⚠️ No FCM token found for user {user.id}")
            except Exception as e:
                print(f"⚠️ Warning: Could not send order notification: {e}")
                # Don't fail order if notification fails

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

            # Restore inventory by creating reverse transactions
            for item in order.items.all():
                design_details = item.design_details
                if design_details and design_details.get('design_color_id'):
                    try:
                        fabric_color_id = design_details.get('design_color_id')
                        fabric_color = FabricColor.objects.filter(id=fabric_color_id).first()

                        if fabric_color:
                            quantity_before = fabric_color.quantity
                            quantity_change = item.quantity  # Positive to add back

                            fabric_color.quantity += quantity_change
                            fabric_color.save()

                            # Create CANCEL transaction
                            InventoryTransaction.objects.create(
                                fabric_color=fabric_color,
                                transaction_type='CANCEL',
                                quantity_change=quantity_change,
                                quantity_before=quantity_before,
                                quantity_after=fabric_color.quantity,
                                reference_order=order.invoice_number,
                                notes=f"Order cancelled: {item.product_name}",
                                created_by=user
                            )
                            print(f"♻️ Inventory restored: +{quantity_change} unit(s) of {fabric_color.color_name_eng} (Stock: {quantity_before} → {fabric_color.quantity})")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not restore inventory for item {item.id}: {e}")

            # Delete CouponUsage entry if coupon was used
            if order.coupon_code:
                try:
                    deleted_count = CouponUsage.objects.filter(order_id=order.invoice_number).delete()[0]
                    if deleted_count > 0:
                        print(f"🎫 CouponUsage deleted: {order.coupon_code} for order {order.invoice_number}")
                    else:
                        print(f"⚠️ No CouponUsage found for order {order.invoice_number}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not delete coupon usage: {e}")

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
                    'id': 0,
                    'delivery_days': 5,
                    'delivery_cost': '2.000',
                    'whatsapp_support': '',
                    'is_active': True,
                    'created_at': None,
                    'updated_at': None
                }, status=status.HTTP_200_OK)

            response_data = {
                'id': settings.id,
                'delivery_days': settings.delivery_days,
                'delivery_cost': str(settings.delivery_cost),
                'whatsapp_support': settings.whatsapp_support or '',
                'is_active': settings.is_active,
                'created_at': settings.created_at.isoformat() if settings.created_at else None,
                'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
            }

            # Add no-cache headers
            response = Response(response_data, status=status.HTTP_200_OK)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

            return response

        except Exception as e:
            print(f"❌ Error fetching delivery settings: {e}")
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

            # Get new status before saving
            new_status = request.data.get('status', order.status)

            serializer.save()

            # Send notification for status change
            try:
                # Get user's FCM token from profile
                user_profile = getattr(order.user, 'profile', None)
                if user_profile and user_profile.fcm_token:
                    send_order_status_notification(
                        user_fcm_token=user_profile.fcm_token,
                        order=order,
                        new_status=new_status
                    )
                    print(f"🔔 Order {new_status} notification sent to user {order.user.id}")
                else:
                    print(f"⚠️ No FCM token found for user {order.user.id}")
            except Exception as e:
                print(f"⚠️ Warning: Could not send status update notification: {e}")
                # Don't fail status update if notification fails

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

            # Restore inventory by creating reverse transactions
            for item in order.items.all():
                design_details = item.design_details
                if design_details and design_details.get('design_color_id'):
                    try:
                        fabric_color_id = design_details.get('design_color_id')
                        fabric_color = FabricColor.objects.filter(id=fabric_color_id).first()

                        if fabric_color:
                            quantity_before = fabric_color.quantity
                            quantity_change = item.quantity  # Positive to add back

                            fabric_color.quantity += quantity_change
                            fabric_color.save()

                            # Create CANCEL transaction
                            InventoryTransaction.objects.create(
                                fabric_color=fabric_color,
                                transaction_type='CANCEL',
                                quantity_change=quantity_change,
                                quantity_before=quantity_before,
                                quantity_after=fabric_color.quantity,
                                reference_order=order.invoice_number,
                                notes=f"Order cancelled: {item.product_name}",
                                created_by=user
                            )
                            print(f"♻️ Inventory restored: +{quantity_change} unit(s) of {fabric_color.color_name_eng} (Stock: {quantity_before} → {fabric_color.quantity})")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not restore inventory for item {item.id}: {e}")

            # Delete CouponUsage entry if coupon was used
            if order.coupon_code:
                try:
                    deleted_count = CouponUsage.objects.filter(order_id=order.invoice_number).delete()[0]
                    if deleted_count > 0:
                        print(f"🎫 CouponUsage deleted: {order.coupon_code} for order {order.invoice_number}")
                    else:
                        print(f"⚠️ No CouponUsage found for order {order.invoice_number}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not delete coupon usage: {e}")

            # Update order status
            order.status = 'Cancelled'
            order.save()

            # Send cancellation notification
            try:
                # Get user's FCM token from profile
                user_profile = getattr(order.user, 'profile', None)
                if user_profile and user_profile.fcm_token:
                    cancellation_reason = request.data.get('reason')
                    send_order_status_notification(
                        user_fcm_token=user_profile.fcm_token,
                        order=order,
                        new_status='Cancelled',
                        reason=cancellation_reason
                    )
                    print(f"🔔 Order Cancelled notification sent to user {order.user.id}")
                else:
                    print(f"⚠️ No FCM token found for user {order.user.id}")
            except Exception as e:
                print(f"⚠️ Warning: Could not send cancellation notification: {e}")
                # Don't fail cancellation if notification fails

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


class UpdateOrderAddressAPIView(APIView):
    """
    POST: Update order delivery address
    Endpoint: /purchase/update-address/
    Body: {
        "invoice_number": "INV-20250121-1234",
        "address_id": "address_id_from_saved_addresses"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from User.models import Address

            user = request.user
            invoice_number = request.data.get('invoice_number')
            address_id = request.data.get('address_id')

            # Validate inputs
            if not invoice_number:
                return Response({
                    'error': 'Invoice number is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not address_id:
                return Response({
                    'error': 'Address ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get the order
            try:
                order = Purchase.objects.get(invoice_number=invoice_number, user=user)
            except Purchase.DoesNotExist:
                return Response({
                    'error': 'Order not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if order can be updated (only Pending and Confirmed orders)
            if order.status not in ['Pending', 'Confirmed']:
                return Response({
                    'error': f'Cannot update address for {order.status} orders'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get the selected address
            try:
                address = Address.objects.get(id=address_id, user=user)
            except Address.DoesNotExist:
                return Response({
                    'error': 'Address not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Update order with selected address
            order.selected_address = address
            order.address_name = address.get_address_type_display()
            order.Area = address.area
            order.block = address.block
            order.street = address.street
            order.house = address.building
            order.apartment = address.apartment
            order.floor = address.floor
            order.longitude = str(address.longitude) if address.longitude else ''
            order.latitude = str(address.latitude) if address.latitude else ''
            order.save()

            print(f"✅ Order {invoice_number} address updated to: {address}")

            serializer = PurchaseSerializer(order)
            return Response({
                'message': 'Order address updated successfully',
                'order': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"❌ Error updating order address: {e}")
            return Response({
                'error': 'Failed to update order address',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AboutUsAPIView(APIView):
    """
    GET: Get About Us content
    Endpoint: /purchase/about-us/
    Public endpoint - no authentication required
    """
    permission_classes = []  # Public endpoint

    def get(self, request):
        try:
            # Get active about us content
            about_us = AboutUs.objects.filter(is_active=True).first()

            if not about_us:
                return Response({
                    'error': 'No About Us content found',
                    'message': 'Please add About Us content from admin panel'
                }, status=status.HTTP_404_NOT_FOUND)

            from .serializers import AboutUsSerializer
            serializer = AboutUsSerializer(about_us)

            # Create response with no-cache headers
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

            return response

        except Exception as e:
            print(f"❌ Error fetching About Us content: {e}")
            return Response({
                'error': 'Failed to fetch About Us content',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TermsAndConditionsAPIView(APIView):
    """
    GET: Get Terms and Conditions content
    Endpoint: /purchase/terms-and-conditions/
    Public endpoint - no authentication required
    """
    permission_classes = []  # Public endpoint

    def get(self, request):
        try:
            # Get active terms and conditions content
            terms = TermsAndConditions.objects.filter(is_active=True).first()

            if not terms:
                return Response({
                    'error': 'No Terms and Conditions content found',
                    'message': 'Please add Terms and Conditions content from admin panel'
                }, status=status.HTTP_404_NOT_FOUND)

            from .serializers import TermsAndConditionsSerializer
            serializer = TermsAndConditionsSerializer(terms)

            # Create response with no-cache headers
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

            return response

        except Exception as e:
            print(f"❌ Error fetching Terms and Conditions content: {e}")
            return Response({
                'error': 'Failed to fetch Terms and Conditions content',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
