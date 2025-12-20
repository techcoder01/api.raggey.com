from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('orders/', views.orders_view, name='orders'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('products/', views.products_view, name='products'),
    path('design-components/', views.design_components_view, name='design_components'),
    path('categories/', views.categories_view, name='categories'),
    path('customers/', views.customers_view, name='customers'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('logout/', views.logout_view, name='logout'),
]

app_name = 'admin_dashboard'
