from rest_framework import serializers
from .models import Purchase, Item, DeliverySettings, Payment, CancellationRequest, AboutUs, TermsAndConditions
from Design.serializers import UserDesignSerializer
from Sizes.serializers import SizesSerializer


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Order Items"""
    user_design = UserDesignSerializer(read_only=True)
    selected_size = SizesSerializer(read_only=True)

    class Meta:
        model = Item
        fields = [
            'id',
            'user_design',
            'selected_size',
            'product_code',
            'product_id',
            'product_name',
            'category',
            'unit_price',
            'net_amount',
            'discount',
            'discount_percentage',  # Discount percentage (15, 5, or 2)
            'quantity',
            'product_size',
            'cover',
            'design_details',  # NEW: Design details as JSON
            'size_details',  # NEW: Size details as JSON
            'created_date'
        ]


class ItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Order Items (accepts IDs)"""

    class Meta:
        model = Item
        fields = [
            'user_design',
            'selected_size',
            'product_name',
            'unit_price',
            'net_amount',
            'discount',
            'quantity',
            'product_size',
            'cover'
        ]


class CancellationRequestSerializer(serializers.ModelSerializer):
    """Serializer for Cancellation Requests"""
    class Meta:
        model = CancellationRequest
        fields = [
            'id',
            'reason',
            'status',
            'admin_notes',
            'created_at',
            'updated_at',
            'processed_at'
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    """Serializer for Purchase Orders (Read)"""
    items = ItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    latest_cancellation_request = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = [
            'id',
            'user',
            'invoice_number',
            'full_name',
            'email',
            'phone_number',
            'address_name',
            'Area',
            'block',
            'street',
            'house',
            'apartment',
            'floor',
            'longitude',
            'latitude',
            'payment_option',
            'total_price',
            'delivery_fee',
            'discount_amount',
            'coupon_code',
            'cancelled_by',
            'cancellation_reason',
            'status',
            'is_pick_up',
            'is_cash',
            'timestamp',
            # Status timestamps
            'pending_at',
            'confirmed_at',
            'working_at',
            'shipping_at',
            'delivered_at',
            'cancelled_at',
            'asap_order_id',
            'items',
            'items_count',
            'latest_cancellation_request'
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_latest_cancellation_request(self, obj):
        """Get latest cancellation request (any status) if exists"""
        latest_request = obj.cancellation_requests.order_by('-created_at').first()
        if latest_request:
            return CancellationRequestSerializer(latest_request).data
        return None


class PurchaseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Purchase Orders"""

    class Meta:
        model = Purchase
        fields = [
            'full_name',
            'email',
            'phone_number',
            'address_name',
            'Area',
            'block',
            'street',
            'house',
            'apartment',
            'floor',
            'longitude',
            'latitude',
            'payment_option',
            'delivery_fee',
            'is_pick_up',
            'is_cash'
        ]


class PurchaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing orders"""
    items = ItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = [
            'id',
            'invoice_number',
            'full_name',
            'email',
            'phone_number',
            'total_price',
            'status',
            'cancelled_by',
            'cancellation_reason',
            'timestamp',
            # Status timestamps
            'pending_at',
            'confirmed_at',
            'working_at',
            'shipping_at',
            'delivered_at',
            'cancelled_at',
            'items',
            'items_count'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class PurchaseStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status"""

    class Meta:
        model = Purchase
        fields = ['status']

    def validate_status(self, value):
        valid_statuses = ['Pending', 'Processing', 'Ready', 'Delivering', 'Complete', 'Cancelled']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value


class DeliverySettingsSerializer(serializers.ModelSerializer):
    """Serializer for Delivery Settings"""

    class Meta:
        model = DeliverySettings
        fields = [
            'id',
            'delivery_days',
            'delivery_cost',
            'whatsapp_support',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# ================== PAYMENT SERIALIZERS ==================

class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment transactions (Read)"""
    purchase_details = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'track_id',
            'payzah_payment_id',
            'amount',
            'currency',
            'status',
            'payzah_reference_code',
            'knet_payment_id',
            'transaction_number',
            'payment_date',
            'payment_status_raw',
            'verified_with_gateway',
            'gateway_verification_attempts',
            'redirect_url',
            'initiated_at',
            'completed_at',
            'created_at',
            'updated_at',
            'purchase_details',
            'user_details'
        ]
        read_only_fields = [
            'track_id',
            'payzah_payment_id',
            'payzah_reference_code',
            'knet_payment_id',
            'transaction_number',
            'payment_date',
            'payment_status_raw',
            'verified_with_gateway',
            'gateway_verification_attempts',
            'initiated_at',
            'completed_at',
            'created_at',
            'updated_at'
        ]

    def get_purchase_details(self, obj):
        if obj.purchase:
            return {
                'invoice_number': obj.purchase.invoice_number,
                'full_name': obj.purchase.full_name,
                'total_price': str(obj.purchase.total_price),
                'status': obj.purchase.status
            }
        return None

    def get_user_details(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating payment"""
    purchase_id = serializers.IntegerField(required=True, help_text="Purchase order ID")
    success_url = serializers.URLField(required=True, help_text="Success redirect URL")
    error_url = serializers.URLField(required=True, help_text="Error redirect URL")

    def validate_purchase_id(self, value):
        """Validate that purchase exists and belongs to user"""
        try:
            purchase = Purchase.objects.get(id=value)
            # Additional validation can be added here
            # e.g., check if purchase already has a payment
            if hasattr(purchase, 'payment') and purchase.payment:
                if purchase.payment.status == 'captured':
                    raise serializers.ValidationError("Payment already completed for this purchase")
            return value
        except Purchase.DoesNotExist:
            raise serializers.ValidationError("Purchase not found")


class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer for payment callback data from Payzah"""
    trackid = serializers.CharField(required=True)
    payment_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    payzahRefrenceCode = serializers.CharField(required=False, allow_blank=True)
    knetPaymentId = serializers.CharField(required=False, allow_blank=True)
    transactionNumber = serializers.CharField(required=False, allow_blank=True)
    paymentDate = serializers.CharField(required=False, allow_blank=True)
    paymentStatus = serializers.CharField(required=False, allow_blank=True)
    UDF1 = serializers.CharField(required=False, allow_blank=True)
    UDF2 = serializers.CharField(required=False, allow_blank=True)
    UDF3 = serializers.CharField(required=False, allow_blank=True)
    UDF4 = serializers.CharField(required=False, allow_blank=True)
    UDF5 = serializers.CharField(required=False, allow_blank=True)


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for verifying payment"""
    track_id = serializers.CharField(required=True, help_text="Payment track ID")
    payment_id = serializers.CharField(required=False, allow_blank=True, help_text="Payzah payment ID")


class PaymentStatusSerializer(serializers.ModelSerializer):
    """Lightweight serializer for payment status"""

    class Meta:
        model = Payment
        fields = [
            'track_id',
            'status',
            'amount',
            'currency',
            'verified_with_gateway',
            'created_at'
        ]
        read_only_fields = fields


class AboutUsSerializer(serializers.ModelSerializer):
    """Serializer for AboutUs model - simple About Us content"""
    class Meta:
        model = AboutUs
        fields = ['id', 'title_en', 'title_ar', 'content_en', 'content_ar', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class TermsAndConditionsSerializer(serializers.ModelSerializer):
    """Serializer for TermsAndConditions model - simple Terms and Conditions content"""
    class Meta:
        model = TermsAndConditions
        fields = ['id', 'title_en', 'title_ar', 'content_en', 'content_ar', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
