from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db import transaction
from django.db import models

from .models import Coupon, CouponUsage
from .serializers import (
    CouponSerializer,
    CouponCardSerializer,
    ValidateCouponSerializer,
    ApplyCouponSerializer,
    CouponUsageSerializer
)


class CouponViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Coupon CRUD operations and coupon validation/application
    """
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get_permissions(self):
        """
        Set permissions based on action
        - list, retrieve, card_coupons, validate_coupon, apply_coupon: AllowAny
        - create, update, partial_update, destroy: IsAdminUser
        """
        if self.action in ['list', 'retrieve', 'card_coupons', 'validate_coupon', 'apply_coupon']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'], url_path='card-coupons')
    def card_coupons(self, request):
        """
        Get all active card-style promotional coupons for display in checkout
        GET /api/coupons/card-coupons/
        """
        now = timezone.now()
        card_coupons = Coupon.objects.filter(
            coupon_type='card',
            is_active=True,
            valid_from__lte=now
        ).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=now)
        )

        # Optionally filter only featured coupons
        featured_only = request.query_params.get('featured', 'false').lower() == 'true'
        if featured_only:
            card_coupons = card_coupons.filter(is_featured=True)

        serializer = CouponCardSerializer(card_coupons, many=True)
        return Response({
            'success': True,
            'count': len(serializer.data),
            'coupons': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='validate')
    def validate_coupon(self, request):
        """
        Validate a coupon code
        POST /api/coupons/validate/
        Body: {
            "code": "BETA50",
            "user_id": "user123",
            "order_amount": 50.000
        }
        """
        serializer = ValidateCouponSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']
        user_id = serializer.validated_data['user_id']
        order_amount = serializer.validated_data['order_amount']

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid coupon code'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if coupon can be used
        can_use, message = coupon.can_be_used_by_user(user_id, order_amount)

        if not can_use:
            return Response({
                'success': False,
                'message': message,
                'coupon': CouponSerializer(coupon).data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate discount
        discount_amount = coupon.calculate_discount(order_amount)

        return Response({
            'success': True,
            'message': 'Coupon is valid',
            'coupon': CouponSerializer(coupon).data,
            'discount_amount': discount_amount,
            'final_amount': float(order_amount) - discount_amount
        })

    @action(detail=False, methods=['post'], url_path='apply')
    def apply_coupon(self, request):
        """
        Apply a coupon and record its usage
        POST /api/coupons/apply/
        Body: {
            "code": "BETA50",
            "user_id": "user123",
            "order_amount": 50.000,
            "order_id": "order_12345" (optional)
        }
        """
        serializer = ApplyCouponSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code'].upper()
        user_id = serializer.validated_data['user_id']
        order_amount = serializer.validated_data['order_amount']
        order_id = serializer.validated_data.get('order_id', None)

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid coupon code'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if coupon can be used
        can_use, message = coupon.can_be_used_by_user(user_id, order_amount)

        if not can_use:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate discount
        discount_amount = coupon.calculate_discount(order_amount)

        # Apply coupon and record usage in a transaction
        try:
            with transaction.atomic():
                # Increment coupon usage count
                coupon.current_uses += 1
                coupon.save()

                # Create usage record
                usage = CouponUsage.objects.create(
                    coupon=coupon,
                    user_id=user_id,
                    order_id=order_id,
                    discount_amount=discount_amount,
                    order_amount=order_amount
                )

                return Response({
                    'success': True,
                    'message': 'Coupon applied successfully',
                    'coupon': CouponSerializer(coupon).data,
                    'usage': CouponUsageSerializer(usage).data,
                    'discount_amount': discount_amount,
                    'final_amount': float(order_amount) - discount_amount
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to apply coupon: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='by-code/(?P<code>[^/.]+)')
    def get_by_code(self, request, code=None):
        """
        Get coupon details by code
        GET /api/coupons/by-code/BETA50/
        """
        try:
            coupon = Coupon.objects.get(code=code.upper())
            serializer = CouponSerializer(coupon)
            return Response({
                'success': True,
                'coupon': serializer.data
            })
        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Coupon not found'
            }, status=status.HTTP_404_NOT_FOUND)


class CouponUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Coupon Usage records
    """
    queryset = CouponUsage.objects.all()
    serializer_class = CouponUsageSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        Get all coupon usages for a specific user
        GET /api/coupon-usages/by-user/user123/
        """
        usages = CouponUsage.objects.filter(user_id=user_id)
        serializer = CouponUsageSerializer(usages, many=True)
        return Response({
            'success': True,
            'count': len(serializer.data),
            'usages': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-order/(?P<order_id>[^/.]+)')
    def by_order(self, request, order_id=None):
        """
        Get coupon usage for a specific order
        GET /api/coupon-usages/by-order/order_12345/
        """
        try:
            usage = CouponUsage.objects.get(order_id=order_id)
            serializer = CouponUsageSerializer(usage)
            return Response({
                'success': True,
                'usage': serializer.data
            })
        except CouponUsage.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No coupon usage found for this order'
            }, status=status.HTTP_404_NOT_FOUND)
