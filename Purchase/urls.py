from django.urls import path
from .views import (
    # User-side views
    CreateOrderAPIView,
    OrderHistoryAPIView,
    OrderDetailAPIView,
    CancelOrderAPIView,
    UpdateOrderAddressAPIView,
    DeliverySettingsAPIView,
    AboutUsAPIView,
    TermsAndConditionsAPIView,

    # Admin-side views
    AdminOrderListAPIView,
    AdminOrderDetailAPIView,
    AdminUpdateOrderStatusAPIView,
    AdminCancelOrderAPIView,
)
from .analytics import (
    # Dashboard Analytics
    DashboardKPIAPIView,
    RevenueTrendAPIView,
    OrderStatusDistributionAPIView,
    PopularFabricsAPIView,
    TopCustomersAPIView,
    RecentOrdersTableAPIView,
    InventoryStatusTableAPIView,
)

urlpatterns = [
    # ================ USER-SIDE ENDPOINTS ================

    # Order Creation
    path('create-order/', CreateOrderAPIView.as_view(), name='create-order'),

    # Order History & Details
    path('orders/', OrderHistoryAPIView.as_view(), name='order-history'),
    path('order/<int:pk>/', OrderDetailAPIView.as_view(), name='order-detail'),

    # Order Cancellation
    path('order/<int:pk>/cancel/', CancelOrderAPIView.as_view(), name='cancel-order'),

    # Order Address Update
    path('update-address/', UpdateOrderAddressAPIView.as_view(), name='update-order-address'),

    # Delivery Settings
    path('delivery-settings/', DeliverySettingsAPIView.as_view(), name='delivery-settings'),

    # About Us
    path('about-us/', AboutUsAPIView.as_view(), name='about-us'),

    # Terms and Conditions
    path('terms-and-conditions/', TermsAndConditionsAPIView.as_view(), name='terms-and-conditions'),

    # ================ ADMIN-SIDE ENDPOINTS ================

    # Order Management
    path('admin/orders/', AdminOrderListAPIView.as_view(), name='admin-order-list'),
    path('admin/order/<int:pk>/', AdminOrderDetailAPIView.as_view(), name='admin-order-detail'),

    # Order Status Update
    path('admin/order/<int:pk>/status/', AdminUpdateOrderStatusAPIView.as_view(), name='admin-update-order-status'),

    # Order Cancellation (Admin)
    path('admin/order/<int:pk>/cancel/', AdminCancelOrderAPIView.as_view(), name='admin-cancel-order'),

    # ================ DASHBOARD ANALYTICS (ADMIN) ================

    # KPIs and Metrics
    path('analytics/kpis/', DashboardKPIAPIView.as_view(), name='dashboard-kpis'),
    path('analytics/revenue-trend/', RevenueTrendAPIView.as_view(), name='revenue-trend'),
    path('analytics/order-status/', OrderStatusDistributionAPIView.as_view(), name='order-status-distribution'),

    # Popular Items
    path('analytics/popular-fabrics/', PopularFabricsAPIView.as_view(), name='popular-fabrics'),

    # Customer Analytics
    path('analytics/top-customers/', TopCustomersAPIView.as_view(), name='top-customers'),

    # Data Tables
    path('analytics/recent-orders/', RecentOrdersTableAPIView.as_view(), name='recent-orders-table'),
    path('analytics/inventory-status/', InventoryStatusTableAPIView.as_view(), name='inventory-status-table'),
]

app_name = 'Purchase-api'
