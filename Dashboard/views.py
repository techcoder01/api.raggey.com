from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from Purchase.models import Purchase, Payment
from Design.models import (
    FabricColor, FabricType, GholaType, SleevesType,
    PocketType, ButtonType, ButtonStripType, BodyType
)
from Coupon.models import Coupon


def is_staff_user(user):
    return user.is_staff or user.is_superuser


def login_view(request):
    if request.user.is_authenticated and is_staff_user(request.user):
        return redirect('/dashboard/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and is_staff_user(user):
            login(request, user)
            return redirect('/dashboard/')
        else:
            context = {
                'error': 'Invalid credentials or insufficient permissions'
            }
            return render(request, 'dashboard/login.html', context)

    return render(request, 'dashboard/login.html')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def logout_view(request):
    logout(request)
    return redirect('/dashboard/login/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def dashboard_view(request):
    # Get date range for filtering
    today = timezone.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = today - timedelta(days=30)

    # Recent orders (last 30 days)
    recent_orders = Purchase.objects.filter(
        timestamp__gte=thirty_days_ago
    ).select_related('user').order_by('-timestamp')[:10]

    # Statistics
    total_orders = Purchase.objects.count()
    pending_orders = Purchase.objects.filter(status='Pending').count()
    total_revenue = Purchase.objects.aggregate(
        total=Sum('total_price'))['total'] or 0

    # Today's statistics
    todays_orders = Purchase.objects.filter(timestamp__gte=today_start).count()
    todays_revenue = Purchase.objects.filter(timestamp__gte=today_start).aggregate(
        total=Sum('total_price'))['total'] or 0

    # Order status breakdown
    status_breakdown = {
        'pending': Purchase.objects.filter(status='Pending').count(),
        'confirmed': Purchase.objects.filter(status='Confirmed').count(),
        'working': Purchase.objects.filter(status='Working').count(),
        'shipping': Purchase.objects.filter(status='Shipping').count(),
        'delivered': Purchase.objects.filter(status='Delivered').count(),
        'cancelled': Purchase.objects.filter(status='Cancelled').count(),
    }

    # Payment status breakdown
    payment_breakdown = {
        'captured': Payment.objects.filter(status='CAPTURED').count(),
        'pending': Payment.objects.filter(status='PENDING').count(),
        'failed': Payment.objects.filter(status='FAILED').count(),
        'refunded': Payment.objects.filter(status='REFUNDED').count(),
    }

    # Recent payments
    recent_payments = Payment.objects.select_related(
        'purchase'
    ).order_by('-created_at')[:10]

    # Active coupons
    active_coupons = Coupon.objects.filter(
        is_active=True,
        valid_until__gte=today
    ).count()

    # Total users
    total_users = User.objects.count()

    # Low stock items - Fabric Colors with quantity < 50
    low_stock_fabrics = FabricColor.objects.filter(
        quantity__lt=50,
        inStock=True
    ).select_related('fabric_type').order_by('quantity')[:10]

    # Out of stock buttons
    out_of_stock_buttons = ButtonType.objects.filter(
        inStock=False
    ).order_by('button_type_name_eng')[:10]

    # Combine low stock items
    low_stock_items = list(low_stock_fabrics) + list(out_of_stock_buttons)

    context = {
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'todays_orders': todays_orders,
        'todays_revenue': todays_revenue,
        'status_breakdown': status_breakdown,
        'payment_breakdown': payment_breakdown,
        'recent_payments': recent_payments,
        'active_coupons': active_coupons,
        'total_users': total_users,
        'low_stock_items': low_stock_items,
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

    # Base queryset
    orders = Purchase.objects.select_related('user', 'selected_address').order_by('-timestamp')

    # Apply status filter
    if status_filter:
        orders = orders.filter(status=status_filter)

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

    # Get statistics for the current filter (with search, user, date applied)
    current_orders = orders.count()
    current_amount = orders.aggregate(total=Sum('total_price'))['total'] or 0

    # Status counts for quick filters (include all for 'all' tab)
    status_counts = {
        'all': Purchase.objects.count(),
        'pending': Purchase.objects.filter(status='Pending').count(),
        'confirmed': Purchase.objects.filter(status='Confirmed').count(),
        'working': Purchase.objects.filter(status='Working').count(),
        'shipping': Purchase.objects.filter(status='Shipping').count(),
        'delivered': Purchase.objects.filter(status='Delivered').count(),
        'cancelled': Purchase.objects.filter(status='Cancelled').count(),
    }

    # Statistics for the selected tab (without search/user/date filters)
    if status_filter:
        # Specific status selected
        tab_orders = Purchase.objects.filter(status=status_filter)
    else:
        # "All" tab - include all orders
        tab_orders = Purchase.objects.all()

    total_orders_for_tab = tab_orders.count()
    total_amount_for_tab = tab_orders.aggregate(total=Sum('total_price'))['total'] or 0

    # Get list of users who have placed orders
    users_with_orders = User.objects.filter(
        purchases__isnull=False
    ).distinct().order_by('email')

    context = {
        'orders': orders,
        'total_orders_for_tab': total_orders_for_tab,
        'current_orders': current_orders,
        'total_amount_for_tab': total_amount_for_tab,
        'current_amount': current_amount,
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
        try:
            order = Purchase.objects.get(id=order_id)
            new_status = request.POST.get('status')

            # Update status
            order.status = new_status

            # Update corresponding timestamp field
            now = timezone.now()
            if new_status == 'Pending' and not order.pending_at:
                order.pending_at = now
            elif new_status == 'Confirmed' and not order.confirmed_at:
                order.confirmed_at = now
            elif new_status == 'Working' and not order.working_at:
                order.working_at = now
            elif new_status == 'Shipping' and not order.shipping_at:
                order.shipping_at = now
            elif new_status == 'Delivered' and not order.delivered_at:
                order.delivered_at = now
            elif new_status == 'Cancelled' and not order.cancelled_at:
                order.cancelled_at = now

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


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def designs_view(request):
    # Get component type filter
    component_type = request.GET.get('type', 'fabric_colors')
    search_query = request.GET.get('search', '')

    # Get appropriate queryset based on component type
    if component_type == 'fabric_colors':
        items = FabricColor.objects.select_related('fabric_type').order_by('-timestamp')
        if search_query:
            items = items.filter(
                Q(color_name_eng__icontains=search_query) |
                Q(color_name_arb__icontains=search_query) |
                Q(fabric_type__fabric_name_eng__icontains=search_query)
            )
        component_label = 'Fabric Colors'
        total_items = FabricColor.objects.count()

    elif component_type == 'fabric_types':
        items = FabricType.objects.order_by('-timestamp')
        if search_query:
            items = items.filter(
                Q(fabric_name_eng__icontains=search_query) |
                Q(fabric_name_arb__icontains=search_query)
            )
        component_label = 'Fabric Types'
        total_items = FabricType.objects.count()

    elif component_type == 'collars':
        items = GholaType.objects.order_by('-timestamp')
        if search_query:
            items = items.filter(
                Q(ghola_type_name_eng__icontains=search_query) |
                Q(ghola_type_name_arb__icontains=search_query)
            )
        component_label = 'Collar Types'
        total_items = GholaType.objects.count()

    elif component_type == 'sleeves':
        items = SleevesType.objects.order_by('-timestamp')
        if search_query:
            items = items.filter(
                Q(sleeves_type_name_eng__icontains=search_query) |
                Q(sleeves_type_name_arb__icontains=search_query)
            )
        component_label = 'Sleeve Types'
        total_items = SleevesType.objects.count()

    elif component_type == 'pockets':
        items = PocketType.objects.order_by('-timestamp')
        if search_query:
            items = items.filter(
                Q(pocket_type_name_eng__icontains=search_query) |
                Q(pocket_type_name_arb__icontains=search_query)
            )
        component_label = 'Pocket Types'
        total_items = PocketType.objects.count()

    elif component_type == 'buttons':
        items = ButtonType.objects.order_by('-timestamp')
        if search_query:
            items = items.filter(
                Q(button_type_name_eng__icontains=search_query) |
                Q(button_type_name_arb__icontains=search_query)
            )
        component_label = 'Button Types'
        total_items = ButtonType.objects.count()

    elif component_type == 'button_strips':
        items = ButtonStripType.objects.order_by('-timestamp')
        if search_query:
            items = items.filter(
                Q(button_strip_type_name_eng__icontains=search_query) |
                Q(button_strip_type_name_arb__icontains=search_query)
            )
        component_label = 'Button Strip Types'
        total_items = ButtonStripType.objects.count()

    elif component_type == 'body':
        items = BodyType.objects.order_by('-timestamp')
        if search_query:
            items = items.filter(
                Q(body_type_name_eng__icontains=search_query) |
                Q(body_type_name_arb__icontains=search_query)
            )
        component_label = 'Body Types'
        total_items = BodyType.objects.count()
    else:
        items = FabricColor.objects.select_related('fabric_type').order_by('-timestamp')
        component_label = 'Fabric Colors'
        total_items = FabricColor.objects.count()

    # Component type counts
    component_counts = {
        'fabric_colors': FabricColor.objects.count(),
        'fabric_types': FabricType.objects.count(),
        'collars': GholaType.objects.count(),
        'sleeves': SleevesType.objects.count(),
        'pockets': PocketType.objects.count(),
        'buttons': ButtonType.objects.count(),
        'button_strips': ButtonStripType.objects.count(),
        'body': BodyType.objects.count(),
    }

    context = {
        'items': items,
        'component_type': component_type,
        'component_label': component_label,
        'component_counts': component_counts,
        'total_items': total_items,
        'search_query': search_query,
        'current_count': items.count(),
    }

    return render(request, 'dashboard/designs.html', context)
