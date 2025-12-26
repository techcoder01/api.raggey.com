from rest_framework import serializers
from .models import Banner

class BannerSerializer(serializers.ModelSerializer):
    """
    Serializer for Banner model
    Returns URLs for both English and Arabic banner images
    """
    image_en_url = serializers.SerializerMethodField()
    image_ar_url = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ['id', 'title', 'image_en_url', 'image_ar_url', 'order', 'is_active']

    def get_image_en_url(self, obj):
        """Get Cloudinary URL for English banner"""
        if obj.image_en:
            return obj.image_en.url
        return None

    def get_image_ar_url(self, obj):
        """Get Cloudinary URL for Arabic banner"""
        if obj.image_ar:
            return obj.image_ar.url
        return None
