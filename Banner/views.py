from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Banner
from .serializers import BannerSerializer

class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving active banners
    Read-only: GET /banners/ (list all active banners)
    No authentication required
    """
    queryset = Banner.objects.filter(is_active=True).order_by('order', '-created_at')
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]  # No authentication required for viewing banners
