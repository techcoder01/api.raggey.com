from django.urls import path, include
from .views import (
    AddressAPIView, DefaultAddressAPIView, UserInfoAPIView,
    SelectedAddressAPIView, UserProfileAPIView, UpdateFCMTokenAPIView,
    BulkSaveCartDataAPIView
)
from .auth_views import UserSignupAPIView, UserLoginAPIView

urlpatterns = [
    # ================ AUTHENTICATION ================
    path('auth/signup/', UserSignupAPIView.as_view(), name='signup'),
    path('auth/login/', UserLoginAPIView.as_view(), name='login'),

    # ================ ADDRESS MANAGEMENT ================
    path('list/address/', AddressAPIView.as_view()),
    path('create/address/', AddressAPIView.as_view()),
    path('update/address/<int:pk>/', AddressAPIView.as_view()),
    path('delete/address/<int:pk>/', AddressAPIView.as_view()),
    path('default/address/<int:pk>/', DefaultAddressAPIView.as_view()),
    path('fetch/default/address/', DefaultAddressAPIView.as_view()),
    path('address/<int:pk>/', SelectedAddressAPIView.as_view()),

    # ================ USER INFO & PROFILE ================
    path('fetch/info/', UserInfoAPIView.as_view()),
    path('profile/', UserProfileAPIView.as_view()),

    # ================ FCM TOKEN MANAGEMENT ================
    path('update-fcm-token/', UpdateFCMTokenAPIView.as_view()),

    # ================ CART DATA ================
    path('bulk-save-cart-data/', BulkSaveCartDataAPIView.as_view()),
]

app_name = 'User-api'
