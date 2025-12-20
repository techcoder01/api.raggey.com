from .models import Address, Profile
from django.contrib.auth.models import User
from rest_framework import serializers
from Purchase.models import Purchase
from Design.serializers import UserDesignSerializer
from Design.models import UserDesign
from Purchase.serializers import PurchaseListSerializer
from Sizes.serializers import CustomMeasurementSerializer, SizesSerializer
from Sizes.models import CustomMeasurement, Sizes


class AddressSerializer(serializers.ModelSerializer):
    """
    Address Serializer
    Handles user addresses with location coordinates and detailed address information
    """
    address_type_display = serializers.CharField(source='get_address_type_display', read_only=True)

    class Meta:
        model = Address
        fields = [
            'id',
            'user',
            'longitude',
            'latitude',
            'full_address',
            'governorate',
            'area',
            'block',
            'street',
            'building',
            'apartment',
            'floor',
            'full_name',
            'phone_number',
            'address_type',
            'address_type_display',
            'custom_label',
            'isDefault',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'address_type_display']

    def create(self, validated_data):
        """Create address and ensure only one default address per user"""
        is_default = validated_data.get('isDefault', False)
        user = validated_data.get('user')

        # If this address is set as default, remove default from other addresses
        if is_default and user:
            Address.objects.filter(user=user, isDefault=True).update(isDefault=False)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update address and handle default address logic"""
        is_default = validated_data.get('isDefault', instance.isDefault)

        # If this address is being set as default, remove default from other addresses
        if is_default and instance.user:
            Address.objects.filter(user=instance.user, isDefault=True).exclude(id=instance.id).update(isDefault=False)

        return super().update(instance, validated_data)



class userBasicInfoSerializer(serializers.ModelSerializer):
    processing_num = serializers.SerializerMethodField()
    delivered_num = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number',
                  'id', "processing_num", "delivered_num"]
        read_only_fields = ['first_name', 'last_name', 'email', 'phone_number', 'id']

    def get_phone_number(self, obj):
        if hasattr(obj, 'profile') and obj.profile.phone_number:
            return obj.profile.phone_number
        return None

    def get_processing_num(self, obj):
        count = 0
        purchases = Purchase.objects.filter(
            email=obj.email, status="Processing")
        count = purchases.count()

        return count

    def get_delivered_num(self, obj):
        count = 0
        purchases = Purchase.objects.filter(
            email=obj.email, status="Delivered")
        count = purchases.count()
        return count


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Comprehensive User Profile Serializer
    Includes: user info, addresses, designs, orders, and custom measurements
    """
    addresses = serializers.SerializerMethodField()
    designs = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()
    custom_measurements = serializers.SerializerMethodField()
    processing_orders_count = serializers.SerializerMethodField()
    completed_orders_count = serializers.SerializerMethodField()
    total_designs_count = serializers.SerializerMethodField()
    total_addresses_count = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'date_joined',
            'addresses',
            'designs',
            'orders',
            'custom_measurements',
            'processing_orders_count',
            'completed_orders_count',
            'total_designs_count',
            'total_addresses_count'
        ]
        read_only_fields = ['id', 'email', 'phone_number', 'date_joined']

    def get_phone_number(self, obj):
        if hasattr(obj, 'profile') and obj.profile.phone_number:
            return obj.profile.phone_number
        return None

    def get_addresses(self, obj):
        addresses = Address.objects.filter(user=obj)
        return AddressSerializer(addresses, many=True).data

    def get_designs(self, obj):
        designs = UserDesign.objects.filter(user=obj).order_by('-timestamp')
        return UserDesignSerializer(designs, many=True).data

    def get_orders(self, obj):
        orders = Purchase.objects.filter(user=obj).order_by('-timestamp')
        return PurchaseListSerializer(orders, many=True).data

    def get_custom_measurements(self, obj):
        # Get new CustomMeasurement records
        custom_measurements = CustomMeasurement.objects.filter(user=obj).order_by('-timestamp')
        custom_data = CustomMeasurementSerializer(custom_measurements, many=True).data

        # Also get old Sizes records for backward compatibility
        old_sizes = Sizes.objects.filter(user=obj).order_by('-timestamp')
        old_sizes_data = SizesSerializer(old_sizes, many=True).data

        # Mark old sizes as legacy
        for size in old_sizes_data:
            size['is_legacy'] = True

        return {
            'custom_measurements': custom_data,
            'legacy_sizes': old_sizes_data
        }

    def get_processing_orders_count(self, obj):
        return Purchase.objects.filter(user=obj, status__in=['Pending', 'Processing', 'Ready', 'Delivering']).count()

    def get_completed_orders_count(self, obj):
        return Purchase.objects.filter(user=obj, status='Complete').count()

    def get_total_designs_count(self, obj):
        return UserDesign.objects.filter(user=obj).count()

    def get_total_addresses_count(self, obj):
        return Address.objects.filter(user=obj).count()


class UpdateFCMTokenSerializer(serializers.Serializer):
    """Serializer for updating FCM token and device info"""
    fcm_token = serializers.CharField(required=True, help_text="Firebase Cloud Messaging token")
    device_name = serializers.CharField(required=False, allow_blank=True, help_text="Device name")
    device_id = serializers.CharField(required=False, allow_blank=True, help_text="Unique device identifier")
    device_type = serializers.CharField(required=False, allow_blank=True, help_text="Device type (android/ios)")

    def update_fcm_token(self, user):
        """Update FCM token in user's profile"""
        fcm_token = self.validated_data.get('fcm_token')
        device_name = self.validated_data.get('device_name', '')
        device_id = self.validated_data.get('device_id', '')
        device_type = self.validated_data.get('device_type', '')

        # Get or create profile
        profile, created = Profile.objects.get_or_create(user=user)

        # Update FCM token and device info
        profile.fcm_token = fcm_token
        if device_name:
            profile.device_name = device_name
        if device_id:
            profile.device_id = device_id
        if device_type:
            profile.device_type = device_type
        profile.save()

        return {
            'success': True,
            'message': 'FCM token updated successfully',
            'fcm_token': fcm_token,
            'device_type': device_type
        }


class UserSignupSerializer(serializers.Serializer):
    """Serializer for user signup"""
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

