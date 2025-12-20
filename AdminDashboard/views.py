from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout


def is_staff(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def dashboard_view(request):
    """Main dashboard page"""
    return render(request, 'admin_dashboard/dashboard.html')


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def orders_view(request):
    """Orders management page"""
    return render(request, 'admin_dashboard/orders.html')


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def inventory_view(request):
    """Inventory management page"""
    return render(request, 'admin_dashboard/inventory.html')


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def customers_view(request):
    """Customers page"""
    return render(request, 'admin_dashboard/customers.html')


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def analytics_view(request):
    """Analytics page"""
    return render(request, 'admin_dashboard/analytics.html')


@login_required
@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logout and redirect to login page"""
    logout(request)
    return redirect('/admin/login/?next=/admin-dashboard/')


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def products_view(request):
    """Products management page (Fabric Types & Colors)"""
    return render(request, 'admin_dashboard/products.html')


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def design_components_view(request):
    """Design components management page (Collars, Sleeves, Pockets, Buttons)"""
    return render(request, 'admin_dashboard/design_components.html')


@login_required
@user_passes_test(is_staff)
@require_http_methods(["GET"])
def categories_view(request):
    """Categories management page (Main Categories & Product Categories)"""
    return render(request, 'admin_dashboard/categories.html')
