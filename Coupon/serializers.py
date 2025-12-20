from rest_framework import serializers
from .models import Coupon, CouponUsage


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for Coupon model"""

    is_valid_status = serializers.SerializerMethodField()
    discount_display = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name_en', 'name_ar', 'description_en', 'description_ar',
            'coupon_type', 'discount_type', 'discount_value', 'discount_display',
            'max_uses', 'current_uses', 'max_uses_per_user',
            'min_order_amount', 'max_discount_amount',
            'valid_from', 'valid_until', 'is_active', 'is_valid_status',
            'is_featured', 'card_color', 'card_icon',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_uses', 'created_at', 'updated_at']

    def get_is_valid_status(self, obj):
        """Get validation status"""
        is_valid, message = obj.is_valid()
        return {
            'valid': is_valid,
            'message': message
        }

    def get_discount_display(self, obj):
        """Get formatted discount display"""
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}%"
        else:
            return f"{obj.discount_value} KWD"


class CouponCardSerializer(serializers.ModelSerializer):
    """Serializer for card-style promotional coupons (minimal fields)"""

    discount_display = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name_en', 'name_ar', 'description_en', 'description_ar',
            'coupon_type', 'discount_type', 'discount_value', 'discount_display',
            'max_uses', 'current_uses', 'max_uses_per_user',
            'min_order_amount', 'max_discount_amount',
            'valid_from', 'valid_until', 'is_active', 'is_featured',
            'card_color', 'card_icon'
        ]

    def get_discount_display(self, obj):
        """Get formatted discount display"""
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}%"
        else:
            return f"{obj.discount_value} KWD"


class ValidateCouponSerializer(serializers.Serializer):
    """Serializer for validating a coupon code"""

    code = serializers.CharField(max_length=50, required=True)
    user_id = serializers.CharField(max_length=255, required=True)
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=3, required=True)

    def validate_code(self, value):
        """Validate that coupon code exists"""
        try:
            coupon = Coupon.objects.get(code=value.upper())
            return value.upper()
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code")


class ApplyCouponSerializer(serializers.Serializer):
    """Serializer for applying a coupon"""

    code = serializers.CharField(max_length=50, required=True)
    user_id = serializers.CharField(max_length=255, required=True)
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=3, required=True)
    order_id = serializers.CharField(max_length=255, required=False, allow_blank=True)


class CouponUsageSerializer(serializers.ModelSerializer):
    """Serializer for Coupon Usage tracking"""

    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    coupon_name_en = serializers.CharField(source='coupon.name_en', read_only=True)
    coupon_name_ar = serializers.CharField(source='coupon.name_ar', read_only=True)

    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon', 'coupon_code', 'coupon_name_en', 'coupon_name_ar',
            'user_id', 'order_id', 'discount_amount', 'order_amount', 'used_at'
        ]
        read_only_fields = ['id', 'used_at']
