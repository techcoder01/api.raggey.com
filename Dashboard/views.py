from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from Purchase.models import Purchase, Payment
from Design.models import FabricColor
from Coupon.models import Coupon


def is_staff_user(user):
    return user.is_staff or user.is_superuser


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Find user by email
        try:
            user_obj = User.objects.get(email=email)
            # Authenticate using username
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None and (user.is_staff or user.is_superuser):
                login(request, user)
                return redirect('/dashboard/')
            else:
                return render(request, 'dashboard/login.html', {
                    'error': 'Invalid credentials or insufficient permissions'
                })
        except User.DoesNotExist:
            return render(request, 'dashboard/login.html', {
                'error': 'Invalid credentials or insufficient permissions'
            })

    return render(request, 'dashboard/login.html')


def logout_view(request):
    logout(request)
    return redirect('/dashboard/login/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def dashboard_view(request):
    # Total Orders (excluding cancelled)
    total_orders = Purchase.objects.exclude(status='Cancelled').count()

    # Total Revenue (captured payments only)
    total_revenue = Payment.objects.filter(status='captured').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Orders by Status
    status_breakdown = {
        'pending': Purchase.objects.filter(status='Pending').count(),
        'confirmed': Purchase.objects.filter(status='Confirmed').count(),
        'working': Purchase.objects.filter(status='Working').count(),
        'shipping': Purchase.objects.filter(status='Shipping').count(),
        'delivered': Purchase.objects.filter(status='Delivered').count(),
        'cancelled': Purchase.objects.filter(status='Cancelled').count(),
    }

    # Payment Status Breakdown
    payment_breakdown = {
        'captured': Payment.objects.filter(status='captured').count(),
        'pending': Payment.objects.filter(status='pending').count(),
        'failed': Payment.objects.filter(status='failed').count(),
        'refunded': Payment.objects.filter(status='refunded').count(),
    }

    # Recent Orders (last 10)
    recent_orders = Purchase.objects.select_related('user', 'selected_address').order_by('-timestamp')[:10]

    # Low Stock Items (quantity < 50)
    low_stock_items = FabricColor.objects.filter(quantity__lt=50).select_related('fabric_type').order_by('quantity')[:10]

    # Today's Orders
    today = timezone.now().date()
    todays_orders = Purchase.objects.filter(timestamp__date=today).exclude(status='Cancelled').count()

    # Today's Revenue
    todays_revenue = Payment.objects.filter(
        status='captured',
        completed_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Active Coupons
    active_coupons = Coupon.objects.filter(is_active=True).count()

    # Total Users
    total_users = User.objects.filter(is_staff=False).count()

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'status_breakdown': status_breakdown,
        'payment_breakdown': payment_breakdown,
        'recent_orders': recent_orders,
        'low_stock_items': low_stock_items,
        'todays_orders': todays_orders,
        'todays_revenue': todays_revenue,
        'active_coupons': active_coupons,
        'total_users': total_users,
    }

    return render(request, 'dashboard/home.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def orders_view(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Base queryset (exclude cancelled by default for "All" view)
    orders = Purchase.objects.select_related('user', 'selected_address').order_by('-timestamp')

    # Apply status filter
    if status_filter:
        orders = orders.filter(status=status_filter)
    else:
        # When no status is selected (All), exclude cancelled orders
        orders = orders.exclude(status='Cancelled')

    # Apply user filter
    if user_filter:
        orders = orders.filter(user_id=user_filter)

    # Apply search filter (invoice number or customer name)
    if search_query:
        orders = orders.filter(
            Q(invoice_number__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # Apply date range filter
    if date_from:
        orders = orders.filter(timestamp__date__gte=date_from)
    if date_to:
        orders = orders.filter(timestamp__date__lte=date_to)

    # Get statistics for the current filter
    total_orders = orders.count()
    total_amount = orders.aggregate(total=Sum('total_price'))['total'] or 0

    # Status counts for quick filters (exclude cancelled from 'all')
    status_counts = {
        'all': Purchase.objects.exclude(status='Cancelled').count(),
        'pending': Purchase.objects.filter(status='Pending').count(),
        'confirmed': Purchase.objects.filter(status='Confirmed').count(),
        'working': Purchase.objects.filter(status='Working').count(),
        'shipping': Purchase.objects.filter(status='Shipping').count(),
        'delivered': Purchase.objects.filter(status='Delivered').count(),
        'cancelled': Purchase.objects.filter(status='Cancelled').count(),
    }

    # Total amount excluding cancelled orders for statistics card
    total_amount_excluding_cancelled = Purchase.objects.exclude(status='Cancelled').aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # Get list of users who have placed orders
    users_with_orders = User.objects.filter(
        purchases__isnull=False
    ).distinct().order_by('email')

    context = {
        'orders': orders,
        'total_orders': total_orders,
        'total_amount': total_amount,
        'total_amount_excluding_cancelled': total_amount_excluding_cancelled,
        'status_counts': status_counts,
        'current_status': status_filter,
        'search_query': search_query,
        'user_filter': user_filter,
        'users_with_orders': users_with_orders,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'dashboard/orders.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def update_order_status(request, order_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        try:
            order = Purchase.objects.get(id=order_id)
            if new_status in ['Pending', 'Confirmed', 'Working', 'Shipping', 'Delivered', 'Cancelled']:
                order.status = new_status
                order.save()
        except Purchase.DoesNotExist:
            pass

    # Redirect back to orders page with current filters
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/orders/'))


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def order_detail_view(request, order_id):
    try:
        order = Purchase.objects.select_related(
            'user',
            'selected_address',
            'payment'
        ).prefetch_related(
            'items__user_design',
            'items__selected_size',
            'cancellation_requests'
        ).get(id=order_id)

        # Get order items
        items = order.items.all()

        # Get payment info if exists
        payment = getattr(order, 'payment', None)

        # Get cancellation requests if any
        cancellation_requests = order.cancellation_requests.all()

        # Calculate status timeline
        status_timeline = []
        if order.pending_at:
            status_timeline.append({'status': 'Pending', 'timestamp': order.pending_at})
        if order.confirmed_at:
            status_timeline.append({'status': 'Confirmed', 'timestamp': order.confirmed_at})
        if order.working_at:
            status_timeline.append({'status': 'Working', 'timestamp': order.working_at})
        if order.shipping_at:
            status_timeline.append({'status': 'Shipping', 'timestamp': order.shipping_at})
        if order.delivered_at:
            status_timeline.append({'status': 'Delivered', 'timestamp': order.delivered_at})
        if order.cancelled_at:
            status_timeline.append({'status': 'Cancelled', 'timestamp': order.cancelled_at})

        context = {
            'order': order,
            'items': items,
            'payment': payment,
            'cancellation_requests': cancellation_requests,
            'status_timeline': status_timeline,
        }

        return render(request, 'dashboard/order_detail.html', context)

    except Purchase.DoesNotExist:
        return redirect('/dashboard/orders/')
