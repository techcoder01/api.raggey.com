from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CouponViewSet, CouponUsageViewSet

router = DefaultRouter()
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'coupon-usages', CouponUsageViewSet, basename='coupon-usage')

urlpatterns = [
    path('', include(router.urls)),
]
