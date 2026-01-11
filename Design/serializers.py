from rest_framework import serializers
from .models import (
    FabricType, FabricColor,
    GholaType, SleevesType, PocketType, ButtonType, BodyType,
    HomePageSelectionCategory, UserDesign
)
from Purchase.models import Item
from django.db.models import Count
import cloudinary
# from .utils import discountPrice, check_discount_experition, check_discount_activation


#================ NEW: FABRIC TYPE SERIALIZERS ================

class FabricTypeSerializer(serializers.ModelSerializer):
    """Serializer for base fabric (without color)"""
    cover = serializers.SerializerMethodField()
    colors_count = serializers.SerializerMethodField()
    season_display = serializers.SerializerMethodField()
    category_type_display = serializers.SerializerMethodField()

    class Meta:
        model = FabricType
        fields = "__all__"
        read_only_fields = ['id', 'timestamp']

    def get_cover(self, obj):
        if obj.cover:
            # Handle case where cover might be a string (public_id) or CloudinaryResource
            if hasattr(obj.cover, 'url'):
                return obj.cover.url
            elif isinstance(obj.cover, str):
                # If it's a string (public_id), construct the Cloudinary URL
                # Cloudinary URLs follow the pattern: https://res.cloudinary.com/{cloud_name}/image/upload/{public_id}
                from cloudinary import CloudinaryImage
                return CloudinaryImage(obj.cover).build_url()
            return str(obj.cover)
        return None

    def get_colors_count(self, obj):
        """Return number of available colors for this fabric"""
        return obj.colors.filter(inStock=True).count()

    def get_season_display(self, obj):
        """Return human-readable season name"""
        return obj.get_season_display() if obj.season else None

    def get_category_type_display(self, obj):
        """Return human-readable category type name"""
        return obj.get_category_type_display() if obj.category_type else None


class FabricColorSerializer(serializers.ModelSerializer):
    """Serializer for fabric color variant"""
    cover = serializers.SerializerMethodField()
    inStock = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    fabric_name_eng = serializers.CharField(source='fabric_type.fabric_name_eng', read_only=True)
    fabric_name_arb = serializers.CharField(source='fabric_type.fabric_name_arb', read_only=True)
    fabric_base_price = serializers.DecimalField(source='fabric_type.base_price', max_digits=9, decimal_places=3, read_only=True)

    class Meta:
        model = FabricColor
        fields = "__all__"
        read_only_fields = ['id', 'timestamp']

    def get_cover(self, obj):
        if obj.cover:
            # Handle case where cover might be a string (public_id) or CloudinaryResource
            if hasattr(obj.cover, 'url'):
                return obj.cover.url
            elif isinstance(obj.cover, str):
                from cloudinary import CloudinaryImage
                return CloudinaryImage(obj.cover).build_url()
            return str(obj.cover)
        return None

    def get_inStock(self, obj):
        """Check if color is in stock based on quantity"""
        if obj.quantity == 0 or obj.inStock == False:
            return False
        elif obj.quantity > 0 and obj.inStock == True:
            return True
        else:
            return False

    def get_total_price(self, obj):
        """Calculate total price: base fabric price + color adjustment"""
        return obj.total_price


class FabricColorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for fabric color with full fabric type details"""
    cover = serializers.SerializerMethodField()
    inStock = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    fabric_type = FabricTypeSerializer(read_only=True)

    class Meta:
        model = FabricColor
        fields = "__all__"
        read_only_fields = ['id', 'timestamp']

    def get_cover(self, obj):
        if obj.cover:
            # Handle case where cover might be a string (public_id) or CloudinaryResource
            if hasattr(obj.cover, 'url'):
                return obj.cover.url
            elif isinstance(obj.cover, str):
                from cloudinary import CloudinaryImage
                return CloudinaryImage(obj.cover).build_url()
            return str(obj.cover)
        return None

    def get_inStock(self, obj):
        if obj.quantity == 0 or obj.inStock == False:
            return False
        elif obj.quantity > 0 and obj.inStock == True:
            return True
        else:
            return False

    def get_total_price(self, obj):
        return obj.total_price


class GholaTypeSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    cover_option = serializers.SerializerMethodField()

    class Meta:
        model = GholaType
        fields = "__all__"
        read_only_fields = ['id']

    def get_cover(self, obj):
        if obj.cover:
            return obj.cover.url
        return None

    def get_cover_option(self, obj):
        if obj.cover_option:
            return obj.cover_option.url
        return None



class SleevesTypeSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    cover_option = serializers.SerializerMethodField()

    class Meta:
        model = SleevesType
        fields = "__all__"
        read_only_fields = ['id']

    def get_cover(self, obj):
        if obj.cover:
            return obj.cover.url
        return None

    def get_cover_option(self, obj):
        if obj.cover_option:
            return obj.cover_option.url
        return None

class PocketTypeSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    cover_option = serializers.SerializerMethodField()

    class Meta:
        model = PocketType
        fields = "__all__"
        read_only_fields = ['id']

    def get_cover(self, obj):
        if obj.cover:
            return obj.cover.url
        return None

    def get_cover_option(self, obj):
        if obj.cover_option:
            return obj.cover_option.url
        return None

class ButtonTypeSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    cover_option = serializers.SerializerMethodField()

    class Meta:
        model = ButtonType
        fields = "__all__"
        read_only_fields = ['id']

    def get_cover(self, obj):
        if obj.cover:
            return obj.cover.url
        return None

    def get_cover_option(self, obj):
        if obj.cover_option:
            return obj.cover_option.url
        return None



class BodyTypeSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    cover_option = serializers.SerializerMethodField()

    class Meta:
        model = BodyType
        fields = "__all__"
        read_only_fields = ['id']

    def get_cover(self, obj):
        if obj.cover:
            return obj.cover.url
        return None

    def get_cover_option(self, obj):
        if obj.cover_option:
            return obj.cover_option.url
        return None

class HomePageSelectionCategorySerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()

    class Meta:
        model = HomePageSelectionCategory
        fields = "__all__"
        read_only_fields = ['id']

    def get_cover(self, obj):
        if obj.cover:
            if hasattr(obj.cover, 'url'):
                return obj.cover.url
            elif isinstance(obj.cover, str):
                return f"https://res.cloudinary.com/drtdkkkbq/image/upload/{obj.cover}"
        return None

class UserDesignSerializer(serializers.ModelSerializer):
    initial_size_selected = HomePageSelectionCategorySerializer()
    main_body_fabric_color = FabricColorSerializer()
    selected_coller_type = GholaTypeSerializer()
    selected_sleeve_left_type = SleevesTypeSerializer()
    selected_sleeve_right_type = SleevesTypeSerializer()
    selected_pocket_type = PocketTypeSerializer()
    selected_button_type = ButtonTypeSerializer()

    selected_body_type = BodyTypeSerializer()

    class Meta:
        model = UserDesign
        fields = "__all__"
        read_only_fields = ['id']
