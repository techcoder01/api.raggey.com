from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('orders/', views.orders_view, name='orders'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('designs/', views.designs_view, name='designs'),
    path('designs/create/', views.create_design_item, name='create_design_item'),
    path('designs/get/<str:component_type>/<int:item_id>/', views.get_design_item, name='get_design_item'),
    path('designs/update/', views.update_design_item, name='update_design_item'),
    path('designs/update-status/', views.update_design_status, name='update_design_status'),
    path('designs/delete/', views.delete_design_item, name='delete_design_item'),
]
