

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, F, Prefetch
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from decimal import Decimal
from Purchase.models import Purchase, Payment
from Design.models import (
    FabricColor, FabricType, GholaType, SleevesType,
    PocketType, ButtonType, BodyType
)
from Design.views import clear_design_cache
from Coupon.models import Coupon


def is_staff_user(user):
    return user.is_staff or user.is_superuser


def login_view(request):
    if request.user.is_authenticated and is_staff_user(request.user):
        return redirect('/dashboard/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Find user by email
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

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

    # Try to get cached statistics (cache for 2 minutes)
    cache_key = f'dashboard_stats_{today_start.date()}'
    cached_data = cache.get(cache_key)

    if cached_data:
        context = cached_data
    else:
        # Recent orders (last 30 days) - optimized query
        recent_orders = Purchase.objects.filter(
            timestamp__gte=thirty_days_ago
        ).select_related('user').only(
            'id', 'invoice_number', 'timestamp', 'status', 'total_price', 'user__username', 'user__email'
        ).order_by('-timestamp')[:10]

        # Optimize statistics queries by combining them
        order_stats = Purchase.objects.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_price'),
            pending_count=Count('id', filter=Q(status='Pending')),
            confirmed_count=Count('id', filter=Q(status='Confirmed')),
            working_count=Count('id', filter=Q(status='Working')),
            shipping_count=Count('id', filter=Q(status='Shipping')),
            delivered_count=Count('id', filter=Q(status='Delivered')),
            cancelled_count=Count('id', filter=Q(status='Cancelled')),
            todays_orders=Count('id', filter=Q(timestamp__gte=today_start)),
            todays_revenue=Sum('total_price', filter=Q(timestamp__gte=today_start))
        )

        # Payment status breakdown - optimized
        payment_stats = Payment.objects.aggregate(
            captured=Count('id', filter=Q(status='CAPTURED')),
            pending=Count('id', filter=Q(status='PENDING')),
            failed=Count('id', filter=Q(status='FAILED')),
            refunded=Count('id', filter=Q(status='REFUNDED'))
        )

        # Recent payments - optimized
        recent_payments = Payment.objects.select_related('purchase').only(
            'id', 'track_id', 'status', 'amount', 'created_at', 'purchase__invoice_number'
        ).order_by('-created_at')[:10]

        # Active coupons (include coupons with no expiry date)
        active_coupons = Coupon.objects.filter(
            is_active=True
        ).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=today)
        ).count()

        # Total users
        total_users = User.objects.count()

        # Low stock items - optimized
        low_stock_fabrics = FabricColor.objects.filter(
            quantity__lt=50,
            inStock=True
        ).select_related('fabric_type').only(
            'id', 'color_name_eng', 'color_name_arb', 'quantity', 'fabric_type__fabric_name_eng'
        ).order_by('quantity')[:10]

        # Out of stock buttons - optimized
        out_of_stock_buttons = ButtonType.objects.filter(
            inStock=False
        ).only('id', 'button_type_name_eng', 'button_type_name_arb').order_by('button_type_name_eng')[:10]

        # Combine low stock items
        low_stock_items = list(low_stock_fabrics) + list(out_of_stock_buttons)

        context = {
            'recent_orders': recent_orders,
            'total_orders': order_stats['total_orders'] or 0,
            'pending_orders': order_stats['pending_count'] or 0,
            'total_revenue': order_stats['total_revenue'] or 0,
            'todays_orders': order_stats['todays_orders'] or 0,
            'todays_revenue': order_stats['todays_revenue'] or 0,
            'status_breakdown': {
                'pending': order_stats['pending_count'] or 0,
                'confirmed': order_stats['confirmed_count'] or 0,
                'working': order_stats['working_count'] or 0,
                'shipping': order_stats['shipping_count'] or 0,
                'delivered': order_stats['delivered_count'] or 0,
                'cancelled': order_stats['cancelled_count'] or 0,
            },
            'payment_breakdown': payment_stats,
            'recent_payments': recent_payments,
            'active_coupons': active_coupons,
            'total_users': total_users,
            'low_stock_items': low_stock_items,
        }

        # Cache for 2 minutes
        cache.set(cache_key, context, 120)

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

    # Check for order item filter
    order_item_id = request.GET.get('order_item')
    filter_ids = {}

    if order_item_id:
        from Purchase.models import Item
        try:
            order_item = Item.objects.get(id=order_item_id)
            if order_item.design_details:
                details = order_item.design_details

                # Fabric color - use exact key name
                if details.get('design_color_id'):
                    filter_ids['fabric_color'] = details.get('design_color_id')

                # Extract all other component IDs from design_details using substring matching
                for key, value in details.items():
                    key_lower = key.lower()
                    if 'id' in key_lower and value:
                        # Skip fabric color as it's already handled
                        if 'design_color' in key_lower:
                            continue
                        elif 'collar' in key_lower or 'coller' in key_lower:
                            filter_ids['collar'] = value
                        elif 'sleeve' in key_lower:
                            if 'sleeves' not in filter_ids:
                                filter_ids['sleeves'] = []
                            filter_ids['sleeves'].append(value)
                        elif 'pocket' in key_lower:
                            filter_ids['pocket'] = value
                        elif 'button' in key_lower:
                            filter_ids['button'] = value

                        elif 'body' in key_lower:
                            filter_ids['body'] = value
        except Item.DoesNotExist:
            pass

    # Get appropriate queryset based on component type
    if component_type == 'fabric_colors':
        items = FabricColor.objects.select_related('fabric_type').order_by('-timestamp')
        # If order filter is active
        if order_item_id:
            if filter_ids.get('fabric_color'):
                items = items.filter(id=filter_ids['fabric_color'])
            else:
                # No fabric color in order, show empty table
                items = items.none()
        if search_query:
            items = items.filter(
                Q(color_name_eng__icontains=search_query) |
                Q(color_name_arb__icontains=search_query) |
                Q(fabric_type__fabric_name_eng__icontains=search_query)
            )
        component_label = 'Fabric Colors'
        total_items = FabricColor.objects.count()
        items = items.order_by('priority', '-timestamp')

    elif component_type == 'fabric_types':
        items = FabricType.objects.all()
        # If order filter is active
        if order_item_id:
            if filter_ids.get('fabric_color'):
                try:
                    fabric_color = FabricColor.objects.get(id=filter_ids['fabric_color'])
                    if fabric_color.fabric_type:
                        items = items.filter(id=fabric_color.fabric_type.id)
                    else:
                        items = items.none()
                except FabricColor.DoesNotExist:
                    items = items.none()
            else:
                # No fabric color in order, show empty table
                items = items.none()
        if search_query:
            items = items.filter(
                Q(fabric_name_eng__icontains=search_query) |
                Q(fabric_name_arb__icontains=search_query)
            )
        component_label = 'Fabric Types'
        total_items = FabricType.objects.count()
        items = items.order_by('priority', '-timestamp')

    elif component_type == 'collars':
        items = GholaType.objects.all()
        # If order filter is active
        if order_item_id:
            if filter_ids.get('collar'):
                items = items.filter(id=filter_ids['collar'])
            else:
                items = items.none()
        if search_query:
            items = items.filter(
                Q(ghola_type_name_eng__icontains=search_query) |
                Q(ghola_type_name_arb__icontains=search_query)
            )
        component_label = 'Collar Types'
        total_items = GholaType.objects.count()
        items = items.order_by('priority', '-timestamp')

    elif component_type == 'sleeves':
        items = SleevesType.objects.all()
        # If order filter is active
        if order_item_id:
            if filter_ids.get('sleeves'):
                items = items.filter(id__in=filter_ids['sleeves'])
            else:
                items = items.none()
        if search_query:
            items = items.filter(
                Q(sleeves_type_name_eng__icontains=search_query) |
                Q(sleeves_type_name_arb__icontains=search_query)
            )
        component_label = 'Sleeve Types'
        total_items = SleevesType.objects.count()
        items = items.order_by('priority', '-timestamp')

    elif component_type == 'pockets':
        items = PocketType.objects.all()
        # If order filter is active
        if order_item_id:
            if filter_ids.get('pocket'):
                items = items.filter(id=filter_ids['pocket'])
            else:
                items = items.none()
        if search_query:
            items = items.filter(
                Q(pocket_type_name_eng__icontains=search_query) |
                Q(pocket_type_name_arb__icontains=search_query)
            )
        component_label = 'Pocket Types'
        total_items = PocketType.objects.count()
        items = items.order_by('priority', '-timestamp')

    elif component_type == 'buttons':
        items = ButtonType.objects.all()
        # If order filter is active
        if order_item_id:
            if filter_ids.get('button'):
                items = items.filter(id=filter_ids['button'])
            else:
                items = items.none()
        if search_query:
            items = items.filter(
                Q(button_type_name_eng__icontains=search_query) |
                Q(button_type_name_arb__icontains=search_query)
            )
        component_label = 'Button Types'
        total_items = ButtonType.objects.count()
        items = items.order_by('priority', '-timestamp')



    elif component_type == 'body':
        items = BodyType.objects.all()
        # If order filter is active
        if order_item_id:
            if filter_ids.get('body'):
                items = items.filter(id=filter_ids['body'])
            else:
                items = items.none()
        if search_query:
            items = items.filter(
                Q(body_type_name_eng__icontains=search_query) |
                Q(body_type_name_arb__icontains=search_query)
            )
        component_label = 'Body Types'
        total_items = BodyType.objects.count()
        items = items.order_by('-timestamp')

    elif component_type == 'main_categories':
        items = HomePageSelectionCategory.objects.all()
        if search_query:
            items = items.filter(
                Q(main_category_name_eng__icontains=search_query) |
                Q(main_category_name_arb__icontains=search_query)
            )
        component_label = 'Main Categories'
        total_items = HomePageSelectionCategory.objects.count()
        items = items.order_by('priority', '-timestamp')
    else:
        items = FabricColor.objects.select_related('fabric_type').order_by('priority', '-timestamp')
        # If order filter is active
        if order_item_id:
            if filter_ids.get('fabric_color'):
                items = items.filter(id=filter_ids['fabric_color'])
            else:
                items = items.none()
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

        'body': BodyType.objects.count(),
        'main_categories': HomePageSelectionCategory.objects.count(),
    }

    # Get all fabric types for the add modal dropdown
    all_fabric_types = FabricType.objects.filter(isHidden=False).order_by('fabric_name_eng')

    context = {
        'items': items,
        'component_type': component_type,
        'component_label': component_label,
        'component_counts': component_counts,
        'total_items': total_items,
        'search_query': search_query,
        'current_count': items.count(),
        'all_fabric_types': all_fabric_types,
        'season_choices': FabricType.SEASON_CHOICES,
        'category_type_choices': FabricType.CATEGORY_TYPE_CHOICES,
        'order_item_id': order_item_id,
    }

    return render(request, 'dashboard/designs.html', context)
# Design CRUD views - to be appended to Dashboard/views.py

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def get_fabric_colors(request, fabric_type_id):
    """Get fabric colors for a specific fabric type"""
    try:
        colors = FabricColor.objects.filter(
            fabric_type_id=fabric_type_id
        ).order_by('color_name_eng').values('id', 'color_name_eng', 'color_name_arb')
        return JsonResponse(list(colors), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def get_design_item(request, component_type, item_id):
    """Get item data for editing"""
    try:
        # Get the appropriate model and item
        if component_type == 'fabric_colors':
            item = FabricColor.objects.get(id=item_id)
            data = {
                'priority': item.priority,
                'name_eng': item.color_name_eng,
                'name_arb': item.color_name_arb,
                'price_adjustment': float(item.price_adjustment),
                'hex_color': item.hex_color,
                'quantity': item.quantity,
                'inStock': item.inStock,
                'cover_url': item.cover.url if item.cover else None,
            }
        elif component_type == 'fabric_types':
            item = FabricType.objects.get(id=item_id)
            data = {
                'priority': item.priority,
                'name_eng': item.fabric_name_eng,
                'name_arb': item.fabric_name_arb,
                'base_price': float(item.base_price),
                'isHidden': item.isHidden,
                'cover_url': item.cover.url if item.cover else None,
            }
        elif component_type == 'collars':
            item = GholaType.objects.get(id=item_id)
            data = {
                'priority': item.priority,
                'name_eng': item.ghola_type_name_eng,
                'name_arb': item.ghola_type_name_arb,
                'initial_price': float(item.initial_price),
                'fabric_type_id': item.fabric_type.id if item.fabric_type else None,
                'fabric_color_id': item.fabric_color.id if item.fabric_color else None,
                'cover_url': item.cover.url if item.cover else None,
                'cover_option_url': item.cover_option.url if item.cover_option else None,
            }
        elif component_type == 'sleeves':
            item = SleevesType.objects.get(id=item_id)
            data = {
                'priority': item.priority,
                'name_eng': item.sleeves_type_name_eng,
                'name_arb': item.sleeves_type_name_arb,
                'initial_price': float(item.initial_price),
                'fabric_type_id': item.fabric_type.id if item.fabric_type else None,
                'fabric_color_id': item.fabric_color.id if item.fabric_color else None,
                'cover_url': item.cover.url if item.cover else None,
                'cover_option_url': item.cover_option.url if item.cover_option else None,
            }
        elif component_type == 'pockets':
            item = PocketType.objects.get(id=item_id)
            data = {
                'priority': item.priority,
                'name_eng': item.pocket_type_name_eng,
                'name_arb': item.pocket_type_name_arb,
                'initial_price': float(item.initial_price),
                'fabric_type_id': item.fabric_type.id if item.fabric_type else None,
                'fabric_color_id': item.fabric_color.id if item.fabric_color else None,
                'cover_url': item.cover.url if item.cover else None,
                'cover_option_url': item.cover_option.url if item.cover_option else None,
            }
        elif component_type == 'buttons':
            item = ButtonType.objects.get(id=item_id)
            data = {
                'priority': item.priority,
                'name_eng': item.button_type_name_eng,
                'name_arb': item.button_type_name_arb,
                'initial_price': float(item.initial_price),
                'inStock': item.inStock,
                'fabric_type_id': item.fabric_type.id if item.fabric_type else None,
                'fabric_color_id': item.fabric_color.id if item.fabric_color else None,
                'cover_url': item.cover.url if item.cover else None,
                'cover_option_url': item.cover_option.url if item.cover_option else None,
            }

        elif component_type == 'body':
            item = BodyType.objects.get(id=item_id)
            data = {
                'name_eng': item.body_type_name_eng,
                'name_arb': item.body_type_name_arb,
                'initial_price': float(item.initial_price),
                'fabric_type_id': item.fabric_type.id if item.fabric_type else None,
                'fabric_color_id': item.fabric_color.id if item.fabric_color else None,
                'cover_url': item.cover.url if item.cover else None,
                'cover_option_url': item.cover_option.url if item.cover_option else None,
            }
        elif component_type == 'main_categories':
            item = HomePageSelectionCategory.objects.get(id=item_id)
            data = {
                'priority': item.priority,
                'name_eng': item.main_category_name_eng,
                'name_arb': item.main_category_name_arb,
                'initial_price': float(item.initial_price),
                'duration_delivery_period': item.duration_delivery_period,
                'review_rate': item.review_rate,
                'review_count': item.review_count,
                'isHidden': item.isHidden,
                'is_comming_soon': item.is_comming_soon,
                'cover_url': item.cover.url if item.cover else None,
            }
        else:
            return JsonResponse({'error': 'Invalid component type'}, status=400)

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_design_item(request):
    """Update design item"""
    try:
        component_type = request.POST.get('component_type')
        item_id = request.POST.get('item_id')
        name_eng = request.POST.get('name_eng')
        name_arb = request.POST.get('name_arb')
        price = request.POST.get('price')
        priority = request.POST.get('priority', 0)

        # Get the item
        if component_type == 'fabric_colors':
            item = FabricColor.objects.get(id=item_id)
            item.color_name_eng = name_eng
            item.color_name_arb = name_arb
            item.price_adjustment = price
            item.hex_color = request.POST.get('hex_color', '#FFFFFF')
            item.quantity = request.POST.get('quantity', 0)
            item.inStock = 'inStock' in request.POST
            item.priority = priority
        elif component_type == 'fabric_types':
            item = FabricType.objects.get(id=item_id)
            item.fabric_name_eng = name_eng
            item.fabric_name_arb = name_arb
            item.base_price = price
            item.isHidden = 'isHidden' in request.POST
            item.priority = priority
        elif component_type == 'collars':
            item = GholaType.objects.get(id=item_id)
            item.ghola_type_name_eng = name_eng
            item.ghola_type_name_arb = name_arb
            item.initial_price = price
            # Handle fabric type and color
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item.fabric_type = FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None
            item.fabric_color = FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            item.priority = priority
        elif component_type == 'sleeves':
            item = SleevesType.objects.get(id=item_id)
            item.sleeves_type_name_eng = name_eng
            item.sleeves_type_name_arb = name_arb
            item.initial_price = price
            # Handle fabric type and color
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item.fabric_type = FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None
            item.fabric_color = FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            item.priority = priority
        elif component_type == 'pockets':
            item = PocketType.objects.get(id=item_id)
            item.pocket_type_name_eng = name_eng
            item.pocket_type_name_arb = name_arb
            item.initial_price = price
            # Handle fabric type and color
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item.fabric_type = FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None
            item.fabric_color = FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            item.priority = priority
        elif component_type == 'buttons':
            item = ButtonType.objects.get(id=item_id)
            item.button_type_name_eng = name_eng
            item.button_type_name_arb = name_arb
            item.initial_price = price
            item.inStock = 'inStock_button' in request.POST
            # Handle fabric type and color
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item.fabric_type = FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None
            item.fabric_color = FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            item.priority = priority

        elif component_type == 'body':
            item = BodyType.objects.get(id=item_id)
            item.body_type_name_eng = name_eng
            item.body_type_name_arb = name_arb
            item.initial_price = price
            # Handle fabric type and color
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item.fabric_type = FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None
            item.fabric_color = FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None

        elif component_type == 'main_categories':
            item = HomePageSelectionCategory.objects.get(id=item_id)
            item.main_category_name_eng = name_eng
            item.main_category_name_arb = name_arb
            item.initial_price = price
            item.priority = priority
            item.duration_delivery_period = request.POST.get('duration_delivery_period', '')
            item.review_rate = request.POST.get('review_rate', 5)
            item.review_count = request.POST.get('review_count', 0)
            item.isHidden = 'isHidden' in request.POST
            item.is_comming_soon = 'is_comming_soon' in request.POST
        else:
            messages.error(request, 'Invalid component type')
            return redirect(f'/dashboard/designs/?type={component_type}')

        # Handle file uploads
        if 'cover' in request.FILES:
            item.cover = request.FILES['cover']

        if 'cover_option' in request.FILES and hasattr(item, 'cover_option'):
            item.cover_option = request.FILES['cover_option']

        if hasattr(item, 'priority'):
            item.priority = priority
        item.save()

        # Clear design cache so API returns fresh data
        clear_design_cache()

        messages.success(request, f'{name_eng} updated successfully')

    except Exception as e:
        messages.error(request, f'Error updating item: {str(e)}')

    return redirect(f'/dashboard/designs/?type={component_type}')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def delete_design_item(request):
    """Delete design item"""
    try:
        component_type = request.POST.get('component_type')
        item_id = request.POST.get('item_id')

        # Get and delete the item
        if component_type == 'fabric_colors':
            item = FabricColor.objects.get(id=item_id)
        elif component_type == 'fabric_types':
            item = FabricType.objects.get(id=item_id)
        elif component_type == 'collars':
            item = GholaType.objects.get(id=item_id)
        elif component_type == 'sleeves':
            item = SleevesType.objects.get(id=item_id)
        elif component_type == 'pockets':
            item = PocketType.objects.get(id=item_id)
        elif component_type == 'buttons':
            item = ButtonType.objects.get(id=item_id)

        elif component_type == 'body':
            item = BodyType.objects.get(id=item_id)
        elif component_type == 'main_categories':
            item = HomePageSelectionCategory.objects.get(id=item_id)
        else:
            messages.error(request, 'Invalid component type')
            return redirect(f'/dashboard/designs/?type={component_type}')

        item.delete()

        # Clear design cache so API returns fresh data
        clear_design_cache()

        messages.success(request, 'Item deleted successfully')

    except Exception as e:
        messages.error(request, f'Error deleting item: {str(e)}')

    return redirect(f'/dashboard/designs/?type={component_type}')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def create_design_item(request):
    """Create new design item"""
    try:
        component_type = request.POST.get('component_type')
        name_eng = request.POST.get('name_eng')
        name_arb = request.POST.get('name_arb')
        price = request.POST.get('price')
        priority = request.POST.get('priority', 0)

        # Create the item based on component type
        if component_type == 'fabric_colors':
            fabric_type_id = request.POST.get('fabric_type')
            fabric_type = FabricType.objects.get(id=fabric_type_id)
            item = FabricColor.objects.create(
                priority=priority,
                color_name_eng=name_eng,
                color_name_arb=name_arb,
                fabric_type=fabric_type,
                price_adjustment=price,
                hex_color=request.POST.get('hex_color', '#FFFFFF'),
                quantity=request.POST.get('quantity', 0),
                inStock='inStock' in request.POST
            )
        elif component_type == 'fabric_types':
            item = FabricType.objects.create(
                priority=priority,
                fabric_name_eng=name_eng,
                fabric_name_arb=name_arb,
                base_price=price,
                isHidden='isHidden' in request.POST
            )
        elif component_type == 'collars':
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item = GholaType.objects.create(
                priority=priority,
                ghola_type_name_eng=name_eng,
                ghola_type_name_arb=name_arb,
                initial_price=price,
                fabric_type=FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None,
                fabric_color=FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            )
            if 'cover' in request.FILES:
                item.cover = request.FILES['cover']
            if 'cover_option' in request.FILES:
                item.cover_option = request.FILES['cover_option']
            item.save()
        elif component_type == 'sleeves':
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item = SleevesType.objects.create(
                priority=priority,
                sleeves_type_name_eng=name_eng,
                sleeves_type_name_arb=name_arb,
                initial_price=price,
                fabric_type=FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None,
                fabric_color=FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            )
            if 'cover' in request.FILES:
                item.cover = request.FILES['cover']
            if 'cover_option' in request.FILES:
                item.cover_option = request.FILES['cover_option']
            item.save()
        elif component_type == 'pockets':
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item = PocketType.objects.create(
                priority=priority,
                pocket_type_name_eng=name_eng,
                pocket_type_name_arb=name_arb,
                initial_price=price,
                fabric_type=FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None,
                fabric_color=FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            )
            if 'cover' in request.FILES:
                item.cover = request.FILES['cover']
            if 'cover_option' in request.FILES:
                item.cover_option = request.FILES['cover_option']
            item.save()
        elif component_type == 'buttons':
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item = ButtonType.objects.create(
                priority=priority,
                button_type_name_eng=name_eng,
                button_type_name_arb=name_arb,
                initial_price=price,
                inStock='inStock_button' in request.POST,
                fabric_type=FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None,
                fabric_color=FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            )
            if 'cover' in request.FILES:
                item.cover = request.FILES['cover']
            if 'cover_option' in request.FILES:
                item.cover_option = request.FILES['cover_option']
            item.save()

        elif component_type == 'body':
            fabric_type_id = request.POST.get('fabric_type_id')
            fabric_color_id = request.POST.get('fabric_color_id')
            item = BodyType.objects.create(
                body_type_name_eng=name_eng,
                body_type_name_arb=name_arb,
                initial_price=price,
                fabric_type=FabricType.objects.get(id=fabric_type_id) if fabric_type_id else None,
                fabric_color=FabricColor.objects.get(id=fabric_color_id) if fabric_color_id else None
            )
            if 'cover' in request.FILES:
                item.cover = request.FILES['cover']
            if 'cover_option' in request.FILES:
                item.cover_option = request.FILES['cover_option']
            item.save()
        elif component_type == 'main_categories':
            item = HomePageSelectionCategory.objects.create(
                priority=priority,
                main_category_name_eng=name_eng,
                main_category_name_arb=name_arb,
                initial_price=price,
                duration_delivery_period=request.POST.get('duration_delivery_period', ''),
                review_rate=request.POST.get('review_rate', 5),
                review_count=request.POST.get('review_count', 0),
                isHidden='isHidden' in request.POST,
                is_comming_soon='is_comming_soon' in request.POST
            )
            if 'cover' in request.FILES:
                item.cover = request.FILES['cover']
            item.save()
        else:
            messages.error(request, 'Invalid component type')
            return redirect(f'/dashboard/designs/?type={component_type}')

        # Clear design cache so API returns fresh data
        clear_design_cache()

        messages.success(request, f'{name_eng} created successfully')

    except Exception as e:
        messages.error(request, f'Error creating item: {str(e)}')

    return redirect(f'/dashboard/designs/?type={component_type}')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_design_status(request):
    """Update design item status"""
    try:
        component_type = request.POST.get('component_type')
        item_id = request.POST.get('item_id')
        status = request.POST.get('status')

        if component_type == 'fabric_colors':
            item = FabricColor.objects.get(id=item_id)
            item.inStock = (status == 'in_stock')
            item.save()

            # Clear design cache so API returns fresh data
            clear_design_cache()

            status_text = 'In Stock' if item.inStock else 'Out of Stock'
            messages.success(request, f'{item.color_name_eng} status updated to {status_text}')
        elif component_type == 'fabric_types':
            item = FabricType.objects.get(id=item_id)
            item.isHidden = (status == 'hidden')
            item.save()

            # Clear design cache so API returns fresh data
            clear_design_cache()

            status_text = 'Hidden' if item.isHidden else 'Active'
            messages.success(request, f'{item.fabric_name_eng} status updated to {status_text}')
        elif component_type == 'buttons':
            item = ButtonType.objects.get(id=item_id)
            item.inStock = (status == 'in_stock')
            item.save()

            # Clear design cache so API returns fresh data
            clear_design_cache()

            status_text = 'In Stock' if item.inStock else 'Out of Stock'
            messages.success(request, f'{item.button_type_name_eng} status updated to {status_text}')
        elif component_type == 'main_categories':
            item = HomePageSelectionCategory.objects.get(id=item_id)
            item.isHidden = (status == 'hidden')
            item.save()

            # Clear design cache so API returns fresh data
            clear_design_cache()

            status_text = 'Hidden' if item.isHidden else 'Active'
            messages.success(request, f'{item.main_category_name_eng} status updated to {status_text}')
        else:
            messages.error(request, 'Invalid component type')

    except Exception as e:
        messages.error(request, f'Error updating status: {str(e)}')

    return redirect(f'/dashboard/designs/?type={component_type}')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_fabric_relation(request):
    """Update fabric type or fabric color for design items"""
    try:
        component_type = request.POST.get('component_type')
        item_id = request.POST.get('item_id')
        field = request.POST.get('field')  # 'fabric_type' or 'fabric_color'
        value = request.POST.get('value')  # ID of the fabric type or color

        # Get the appropriate model
        if component_type == 'collars':
            item = GholaType.objects.get(id=item_id)
            item_name = item.ghola_type_name_eng
        elif component_type == 'sleeves':
            item = SleevesType.objects.get(id=item_id)
            item_name = item.sleeves_type_name_eng
        elif component_type == 'pockets':
            item = PocketType.objects.get(id=item_id)
            item_name = item.pocket_type_name_eng
        elif component_type == 'buttons':
            item = ButtonType.objects.get(id=item_id)
            item_name = item.button_type_name_eng

        elif component_type == 'body':
            item = BodyType.objects.get(id=item_id)
            item_name = item.body_type_name_eng
        else:
            messages.error(request, 'Invalid component type')
            return redirect(f'/dashboard/designs/?type={component_type}')

        # Update the field
        if field == 'fabric_type':
            if value:
                fabric_type = FabricType.objects.get(id=value)
                item.fabric_type = fabric_type
            else:
                item.fabric_type = None
        elif field == 'fabric_color':
            if value:
                fabric_color = FabricColor.objects.get(id=value)
                item.fabric_color = fabric_color
            else:
                item.fabric_color = None
        else:
            messages.error(request, 'Invalid field')
            return redirect(f'/dashboard/designs/?type={component_type}')

        item.save()

        # Clear design cache so API returns fresh data
        clear_design_cache()

    except Exception as e:
        messages.error(request, f'Error updating: {str(e)}')

    return redirect(f'/dashboard/designs/?type={component_type}')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_image(request):
    """Update cover or cover_option image for design items"""
    try:
        component_type = request.POST.get('component_type')
        item_id = request.POST.get('item_id')
        image_field = request.POST.get('image_field')  # 'cover' or 'cover_option'
        image_file = request.FILES.get('image')

        if not image_file:
            messages.error(request, 'No image file provided')
            return redirect(f'/dashboard/designs/?type={component_type}')

        # Get the appropriate model
        if component_type == 'collars':
            item = GholaType.objects.get(id=item_id)
            item_name = item.ghola_type_name_eng
        elif component_type == 'sleeves':
            item = SleevesType.objects.get(id=item_id)
            item_name = item.sleeves_type_name_eng
        elif component_type == 'pockets':
            item = PocketType.objects.get(id=item_id)
            item_name = item.pocket_type_name_eng
        elif component_type == 'buttons':
            item = ButtonType.objects.get(id=item_id)
            item_name = item.button_type_name_eng

        elif component_type == 'body':
            item = BodyType.objects.get(id=item_id)
            item_name = item.body_type_name_eng
        else:
            messages.error(request, 'Invalid component type')
            return redirect(f'/dashboard/designs/?type={component_type}')

        # Update the image field
        if image_field == 'cover':
            item.cover = image_file
            messages.success(request, f'{item_name} cover image updated successfully')
        elif image_field == 'cover_option':
            item.cover_option = image_file
            messages.success(request, f'{item_name} cover option image updated successfully')
        else:
            messages.error(request, 'Invalid image field')
            return redirect(f'/dashboard/designs/?type={component_type}')

        item.save()

        # Clear design cache so API returns fresh data
        clear_design_cache()

    except Exception as e:
        messages.error(request, f'Error updating image: {str(e)}')

    return redirect(f'/dashboard/designs/?type={component_type}')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def delete_image(request):
    """Delete cover or cover_option image for design items"""
    try:
        component_type = request.POST.get('component_type')
        item_id = request.POST.get('item_id')
        image_field = request.POST.get('image_field')  # 'cover' or 'cover_option'

        # Get the appropriate model
        if component_type == 'collars':
            item = GholaType.objects.get(id=item_id)
            item_name = item.ghola_type_name_eng
        elif component_type == 'sleeves':
            item = SleevesType.objects.get(id=item_id)
            item_name = item.sleeves_type_name_eng
        elif component_type == 'pockets':
            item = PocketType.objects.get(id=item_id)
            item_name = item.pocket_type_name_eng
        elif component_type == 'buttons':
            item = ButtonType.objects.get(id=item_id)
            item_name = item.button_type_name_eng

        elif component_type == 'body':
            item = BodyType.objects.get(id=item_id)
            item_name = item.body_type_name_eng
        else:
            messages.error(request, 'Invalid component type')
            return redirect(f'/dashboard/designs/?type={component_type}')

        # Delete the image field
        if image_field == 'cover':
            if item.cover:
                item.cover.delete(save=False)
                item.cover = None
                item.save()
                messages.success(request, f'{item_name} cover image deleted successfully')
            else:
                messages.warning(request, f'{item_name} has no cover image to delete')
        elif image_field == 'cover_option':
            if item.cover_option:
                item.cover_option.delete(save=False)
                item.cover_option = None
                item.save()
                messages.success(request, f'{item_name} cover option image deleted successfully')
            else:
                messages.warning(request, f'{item_name} has no cover option image to delete')
        else:
            messages.error(request, 'Invalid image field')
            return redirect(f'/dashboard/designs/?type={component_type}')

    except Exception as e:
        messages.error(request, f'Error deleting image: {str(e)}')

    return redirect(f'/dashboard/designs/?type={component_type}')


# ==================== USERS MANAGEMENT ====================

@login_required
@user_passes_test(is_staff_user)
def users_view(request):
    """Display list of all users with search and filtering"""
    from User.models import Profile

    search_query = request.GET.get('search', '')

    # Get all users (exclude superusers and staff by default)
    users = User.objects.select_related('profile').all().order_by('-date_joined')

    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Add annotations for order count and total spent
    users = users.annotate(
        order_count=Count('purchases'),
        total_spent=Sum('purchases__total_price')
    )

    # Get permission choices for the modal
    permission_choices = [
        ("User", "User"),
        ("Admin", "Admin"),
        ("Data-Entry", "Data-Entry"),
        ("Partner", "Partner"),
        ("Accountant", "Accountant"),
        ("Driver", "Driver"),
        ("Vendor", "Vendor"),
    ]

    context = {
        'users': users,
        'search_query': search_query,
        'total_users': User.objects.count(),
        'permission_choices': permission_choices,
    }

    return render(request, 'dashboard/users.html', context)


@login_required
@user_passes_test(is_staff_user)
def user_detail_view(request, user_id):
    """Display detailed information about a specific user"""
    from Purchase.models import Purchase
    from Design.models import UserDesign
    from User.models import Address

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('/dashboard/users/')

    # Get user's orders
    orders = Purchase.objects.filter(user=user).order_by('-timestamp')

    # Get user's designs
    designs = UserDesign.objects.filter(user=user).order_by('-timestamp')

    # Get user's addresses
    addresses = Address.objects.filter(user=user).order_by('-created_at')

    # Calculate stats
    total_orders = orders.count()
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0

    # Order status breakdown
    order_status_counts = {
        'pending': orders.filter(status='Pending').count(),
        'confirmed': orders.filter(status='Confirmed').count(),
        'working': orders.filter(status='Working').count(),
        'shipping': orders.filter(status='Shipping').count(),
        'delivered': orders.filter(status='Delivered').count(),
        'cancelled': orders.filter(status='Cancelled').count(),
    }

    context = {
        'user_detail': user,
        'orders': orders[:10],  # Latest 10 orders
        'designs': designs[:10],  # Latest 10 designs
        'addresses': addresses,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'order_status_counts': order_status_counts,
    }

    return render(request, 'dashboard/user_detail.html', context)


# ==================== USER SIZES MANAGEMENT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def user_sizes_view(request):
    """Display list of all user custom measurements"""
    from Sizes.models import Sizes

    search_query = request.GET.get('search', '')
    user_filter = request.GET.get('user', '')

    # Get all custom measurements
    measurements = Sizes.objects.select_related('user').order_by('-timestamp')

    # Apply search filter
    if search_query:
        measurements = measurements.filter(
            Q(size_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # Filter by specific user
    if user_filter:
        measurements = measurements.filter(user__id=user_filter)

    # Get all users for filter dropdown
    users = User.objects.filter(sizes__isnull=False).distinct().order_by('username')

    context = {
        'measurements': measurements,
        'search_query': search_query,
        'user_filter': user_filter,
        'users': users,
        'total_measurements': Sizes.objects.count(),
    }

    return render(request, 'dashboard/user_sizes.html', context)


# ==================== DEFAULT MEASUREMENTS MANAGEMENT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def default_measurements_view(request):
    """Display and manage default measurements (admin-created, visible to all users)"""
    from Sizes.models import DefaultMeasurement

    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    # Get all default measurements
    measurements = DefaultMeasurement.objects.all().order_by('timestamp')

    # Apply search filter
    if search_query:
        measurements = measurements.filter(
            Q(size_name__icontains=search_query) |
            Q(size_name_eng__icontains=search_query) |
            Q(size_name_ar__icontains=search_query)
        )

    # Filter by category
    if category_filter:
        measurements = measurements.filter(category=category_filter)

    # Count by status
    total_measurements = DefaultMeasurement.objects.count()
    active_measurements = DefaultMeasurement.objects.filter(is_active=True).count()
    inactive_measurements = DefaultMeasurement.objects.filter(is_active=False).count()

    # Count by category
    child_count = DefaultMeasurement.objects.filter(category='child').count()
    adult_count = DefaultMeasurement.objects.filter(category='adult').count()
    baby_count = DefaultMeasurement.objects.filter(category='baby').count()

    context = {
        'measurements': measurements,
        'search_query': search_query,
        'category_filter': category_filter,
        'total_measurements': total_measurements,
        'active_measurements': active_measurements,
        'inactive_measurements': inactive_measurements,
        'child_count': child_count,
        'adult_count': adult_count,
        'baby_count': baby_count,
    }

    return render(request, 'dashboard/default_measurements.html', context)


# ==================== PAYMENTS MANAGEMENT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def payments_view(request):
    """Display list of all payment transactions"""

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    user_filter = request.GET.get('user', '')

    # Get all payments
    payments = Payment.objects.select_related('user', 'purchase').order_by('-created_at')

    # Apply search filter
    if search_query:
        payments = payments.filter(
            Q(track_id__icontains=search_query) |
            Q(payzah_payment_id__icontains=search_query) |
            Q(transaction_number__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(purchase__invoice_number__icontains=search_query)
        )

    # Filter by status
    if status_filter:
        payments = payments.filter(status=status_filter)

    # Filter by specific user
    if user_filter:
        payments = payments.filter(user__id=user_filter)

    # Get all users who have made payments for filter dropdown
    users = User.objects.filter(payments__isnull=False).distinct().order_by('username')

    # Calculate statistics
    total_payments = Payment.objects.count()
    total_amount = Payment.objects.filter(status='captured').aggregate(
        total=Sum('amount'))['total'] or 0
    captured_count = Payment.objects.filter(status='captured').count()
    pending_count = Payment.objects.filter(status='pending').count()
    failed_count = Payment.objects.filter(status='failed').count()

    context = {
        'payments': payments,
        'search_query': search_query,
        'status_filter': status_filter,
        'user_filter': user_filter,
        'users': users,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'captured_count': captured_count,
        'pending_count': pending_count,
        'failed_count': failed_count,
        'status_choices': ['pending', 'captured', 'failed', 'canceled', 'refunded'],
    }

    return render(request, 'dashboard/payments.html', context)


# ==================== COUPONS MANAGEMENT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def coupons_view(request):
    """Display list of all coupons"""
    from Coupon.models import Coupon, CouponUsage

    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')

    # Get all coupons
    coupons = Coupon.objects.all().order_by('-created_at')

    # Apply search filter
    if search_query:
        coupons = coupons.filter(
            Q(code__icontains=search_query) |
            Q(name_en__icontains=search_query) |
            Q(name_ar__icontains=search_query)
        )

    # Filter by type
    if type_filter:
        coupons = coupons.filter(coupon_type=type_filter)

    # Filter by status
    if status_filter == 'active':
        coupons = coupons.filter(is_active=True)
    elif status_filter == 'inactive':
        coupons = coupons.filter(is_active=False)

    # Add usage stats to each coupon
    for coupon in coupons:
        coupon.total_discount = CouponUsage.objects.filter(coupon=coupon).aggregate(
            total=Sum('discount_amount'))['total'] or 0

    # Calculate statistics
    total_coupons = Coupon.objects.count()
    active_coupons = Coupon.objects.filter(is_active=True).count()
    total_usage = CouponUsage.objects.count()
    total_discount_given = CouponUsage.objects.aggregate(
        total=Sum('discount_amount'))['total'] or 0

    context = {
        'coupons': coupons,
        'search_query': search_query,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'total_coupons': total_coupons,
        'active_coupons': active_coupons,
        'total_usage': total_usage,
        'total_discount_given': total_discount_given,
        'type_choices': ['beta', 'card', 'general'],
    }

    return render(request, 'dashboard/coupons.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def create_coupon(request):
    """Create a new coupon"""
    from Coupon.models import Coupon
    from django.utils import timezone
    from datetime import datetime

    try:
        # Parse dates
        valid_from = request.POST.get('valid_from')
        valid_until = request.POST.get('valid_until')

        # Convert to datetime objects
        valid_from_dt = timezone.make_aware(datetime.strptime(valid_from, '%Y-%m-%dT%H:%M')) if valid_from else timezone.now()
        valid_until_dt = timezone.make_aware(datetime.strptime(valid_until, '%Y-%m-%dT%H:%M')) if valid_until else None

        coupon = Coupon.objects.create(
            code=request.POST.get('code').upper(),
            name_en=request.POST.get('name_en'),
            name_ar=request.POST.get('name_ar'),
            description_en=request.POST.get('description_en', ''),
            description_ar=request.POST.get('description_ar', ''),
            coupon_type=request.POST.get('coupon_type'),
            discount_type=request.POST.get('discount_type'),
            discount_value=request.POST.get('discount_value'),
            max_uses=request.POST.get('max_uses') if request.POST.get('max_uses') else None,
            max_uses_per_user=request.POST.get('max_uses_per_user', 1),
            min_order_amount=request.POST.get('min_order_amount', 0),
            max_discount_amount=request.POST.get('max_discount_amount') if request.POST.get('max_discount_amount') else None,
            valid_from=valid_from_dt,
            valid_until=valid_until_dt,
            is_active=request.POST.get('is_active') == 'on'
        )

        messages.success(request, f'Coupon {coupon.code} created successfully!')
    except Exception as e:
        messages.error(request, f'Error creating coupon: {str(e)}')

    return redirect('/dashboard/coupons/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_coupon(request, coupon_id):
    """Update an existing coupon"""
    from Coupon.models import Coupon
    from django.utils import timezone
    from datetime import datetime

    try:
        coupon = Coupon.objects.get(id=coupon_id)

        # Parse dates
        valid_from = request.POST.get('valid_from')
        valid_until = request.POST.get('valid_until')

        # Update fields
        coupon.code = request.POST.get('code').upper()
        coupon.name_en = request.POST.get('name_en')
        coupon.name_ar = request.POST.get('name_ar')
        coupon.description_en = request.POST.get('description_en', '')
        coupon.description_ar = request.POST.get('description_ar', '')
        coupon.coupon_type = request.POST.get('coupon_type')
        coupon.discount_type = request.POST.get('discount_type')
        coupon.discount_value = request.POST.get('discount_value')
        coupon.max_uses = request.POST.get('max_uses') if request.POST.get('max_uses') else None
        coupon.max_uses_per_user = request.POST.get('max_uses_per_user', 1)
        coupon.min_order_amount = request.POST.get('min_order_amount', 0)
        coupon.max_discount_amount = request.POST.get('max_discount_amount') if request.POST.get('max_discount_amount') else None
        coupon.valid_from = timezone.make_aware(datetime.strptime(valid_from, '%Y-%m-%dT%H:%M')) if valid_from else timezone.now()
        coupon.valid_until = timezone.make_aware(datetime.strptime(valid_until, '%Y-%m-%dT%H:%M')) if valid_until else None
        coupon.is_active = request.POST.get('is_active') == 'on'

        coupon.save()

        messages.success(request, f'Coupon {coupon.code} updated successfully!')
    except Coupon.DoesNotExist:
        messages.error(request, 'Coupon not found')
    except Exception as e:
        messages.error(request, f'Error updating coupon: {str(e)}')

    return redirect('/dashboard/coupons/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def delete_coupon(request, coupon_id):
    """Delete a coupon"""
    from Coupon.models import Coupon

    try:
        coupon = Coupon.objects.get(id=coupon_id)
        coupon_code = coupon.code
        coupon.delete()
        messages.success(request, f'Coupon {coupon_code} deleted successfully!')
    except Coupon.DoesNotExist:
        messages.error(request, 'Coupon not found')
    except Exception as e:
        messages.error(request, f'Error deleting coupon: {str(e)}')

    return redirect('/dashboard/coupons/')


# ==================== ADDRESSES MANAGEMENT ====================

@login_required
@user_passes_test(is_staff_user)
def addresses_view(request):
    """Display list of all addresses with search and filtering"""
    from User.models import Address

    search_query = request.GET.get('search', '')
    user_filter = request.GET.get('user', '')

    # Get all addresses
    addresses = Address.objects.select_related('user').order_by('-created_at')

    # Apply search filter
    if search_query:
        addresses = addresses.filter(
            Q(full_name__icontains=search_query) |
            Q(area__icontains=search_query) |
            Q(governorate__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    # Apply user filter
    if user_filter:
        addresses = addresses.filter(user_id=user_filter)

    # Get unique users who have addresses
    users_with_addresses = User.objects.filter(
        id__in=Address.objects.values_list('user_id', flat=True).distinct()
    ).order_by('username')

    context = {
        'addresses': addresses,
        'search_query': search_query,
        'user_filter': user_filter,
        'users_with_addresses': users_with_addresses,
        'total_addresses': Address.objects.count(),
    }

    return render(request, 'dashboard/addresses.html', context)


# ==================== BANNERS MANAGEMENT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def banners_view(request):
    """Display list of all banners with search and filtering"""
    from Banner.models import Banner

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    # Get all banners
    banners = Banner.objects.all()

    # Apply search filter
    if search_query:
        banners = banners.filter(title__icontains=search_query)

    # Apply status filter
    if status_filter == 'active':
        banners = banners.filter(is_active=True)
    elif status_filter == 'inactive':
        banners = banners.filter(is_active=False)

    # Statistics
    total_banners = Banner.objects.count()
    active_banners = Banner.objects.filter(is_active=True).count()

    context = {
        'banners': banners,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_banners': total_banners,
        'active_banners': active_banners,
    }

    return render(request, 'dashboard/banners.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def create_banner(request):
    """Create a new banner"""
    from Banner.models import Banner
    import cloudinary.uploader

    try:
        # Handle image uploads
        image_en_file = request.FILES.get('image_en')
        image_ar_file = request.FILES.get('image_ar')

        if not image_en_file or not image_ar_file:
            messages.error(request, 'Both English and Arabic images are required')
            return redirect('/dashboard/banners/')

        # Upload images to Cloudinary
        image_en_result = cloudinary.uploader.upload(image_en_file, folder='banners')
        image_ar_result = cloudinary.uploader.upload(image_ar_file, folder='banners')

        banner = Banner.objects.create(
            title=request.POST.get('title'),
            image_en=image_en_result['public_id'],
            image_ar=image_ar_result['public_id'],
            order=request.POST.get('order', 0),
            is_active=request.POST.get('is_active') == 'on'
        )

        messages.success(request, f'Banner "{banner.title}" created successfully!')
    except Exception as e:
        messages.error(request, f'Error creating banner: {str(e)}')

    return redirect('/dashboard/banners/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_banner(request, banner_id):
    """Update an existing banner"""
    from Banner.models import Banner
    import cloudinary.uploader

    try:
        banner = Banner.objects.get(id=banner_id)

        # Update basic fields
        banner.title = request.POST.get('title')
        banner.order = request.POST.get('order', 0)
        banner.is_active = request.POST.get('is_active') == 'on'

        # Handle image uploads if provided
        image_en_file = request.FILES.get('image_en')
        image_ar_file = request.FILES.get('image_ar')

        if image_en_file:
            # Delete old image from Cloudinary
            if banner.image_en:
                try:
                    cloudinary.uploader.destroy(banner.image_en.public_id)
                except:
                    pass
            # Upload new image
            image_en_result = cloudinary.uploader.upload(image_en_file, folder='banners')
            banner.image_en = image_en_result['public_id']

        if image_ar_file:
            # Delete old image from Cloudinary
            if banner.image_ar:
                try:
                    cloudinary.uploader.destroy(banner.image_ar.public_id)
                except:
                    pass
            # Upload new image
            image_ar_result = cloudinary.uploader.upload(image_ar_file, folder='banners')
            banner.image_ar = image_ar_result['public_id']

        banner.save()

        messages.success(request, f'Banner "{banner.title}" updated successfully!')
    except Banner.DoesNotExist:
        messages.error(request, 'Banner not found')
    except Exception as e:
        messages.error(request, f'Error updating banner: {str(e)}')

    return redirect('/dashboard/banners/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def delete_banner(request, banner_id):
    """Delete a banner"""
    from Banner.models import Banner
    import cloudinary.uploader

    try:
        banner = Banner.objects.get(id=banner_id)
        banner_title = banner.title

        # Delete images from Cloudinary
        try:
            if banner.image_en:
                cloudinary.uploader.destroy(banner.image_en.public_id)
            if banner.image_ar:
                cloudinary.uploader.destroy(banner.image_ar.public_id)
        except:
            pass

        banner.delete()
        messages.success(request, f'Banner "{banner_title}" deleted successfully!')
    except Banner.DoesNotExist:
        messages.error(request, 'Banner not found')
    except Exception as e:
        messages.error(request, f'Error deleting banner: {str(e)}')

    return redirect('/dashboard/banners/')


# ==================== USER DESIGNS MANAGEMENT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def user_designs_view(request):
    """Display list of all user designs with search and filtering"""
    from Design.models import UserDesign

    search_query = request.GET.get('search', '')
    user_filter = request.GET.get('user', '')

    # Get all user designs
    designs = UserDesign.objects.select_related(
        'user',
        'initial_size_selected',
        'main_body_fabric_color',
        'selected_coller_type',
        'selected_sleeve_left_type',
        'selected_sleeve_right_type',
        'selected_pocket_type',
        'selected_button_type',
        'selected_body_type'
    ).order_by('-timestamp')

    # Apply search filter
    if search_query:
        designs = designs.filter(
            Q(design_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # Apply user filter
    if user_filter:
        designs = designs.filter(user_id=user_filter)

    # Get unique users who have designs
    users_with_designs = User.objects.filter(
        id__in=UserDesign.objects.values_list('user_id', flat=True).distinct()
    ).order_by('username')

    # Statistics
    total_designs = UserDesign.objects.count()
    total_users = UserDesign.objects.values('user').distinct().count()
    total_value = UserDesign.objects.aggregate(total=Sum('design_Total'))['total'] or 0

    # Find duplicate design configurations (ignoring user and price)
    duplicate_configs = UserDesign.objects.values(
        'initial_size_selected',
        'main_body_fabric_color',
        'selected_coller_type',
        'selected_sleeve_left_type',
        'selected_sleeve_right_type',
        'selected_pocket_type',
        'selected_button_type',
        'selected_body_type'
    ).annotate(
        count=Count('id')
    ).filter(count__gt=1)

    # Calculate total unique configurations
    unique_configurations = UserDesign.objects.values(
        'initial_size_selected',
        'main_body_fabric_color',
        'selected_coller_type',
        'selected_sleeve_left_type',
        'selected_sleeve_right_type',
        'selected_pocket_type',
        'selected_button_type',
        'selected_body_type'
    ).distinct().count()

    context = {
        'designs': designs,
        'search_query': search_query,
        'user_filter': user_filter,
        'users_with_designs': users_with_designs,
        'total_designs': total_designs,
        'total_users': total_users,
        'total_value': total_value,
        'unique_configurations': unique_configurations,
        'duplicate_count': duplicate_configs.count(),
    }

    return render(request, 'dashboard/user_designs.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def delete_user_design(request, design_id):
    """Delete a user design"""
    from Design.models import UserDesign

    try:
        design = UserDesign.objects.get(id=design_id)
        design_name = design.design_name or f"Design #{design.id}"
        design.delete()
        messages.success(request, f'Design "{design_name}" deleted successfully!')
    except UserDesign.DoesNotExist:
        messages.error(request, 'Design not found')
    except Exception as e:
        messages.error(request, f'Error deleting design: {str(e)}')

    return redirect('/dashboard/user-designs/')


# ==================== INVENTORY TRACKING ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def inventory_view(request):
    """Display inventory tracking with stock levels and transaction history"""
    from Design.models import FabricColor, InventoryTransaction

    search_query = request.GET.get('search', '')
    transaction_type_filter = request.GET.get('transaction_type', '')
    fabric_filter = request.GET.get('fabric', '')

    # Get all fabric colors with their current stock
    fabrics = FabricColor.objects.select_related('fabric_type').all()

    # Get all transactions
    transactions = InventoryTransaction.objects.select_related(
        'fabric_color__fabric_type',
        'created_by'
    ).order_by('-timestamp')

    # Apply search filter
    if search_query:
        transactions = transactions.filter(
            Q(fabric_color__color_name_eng__icontains=search_query) |
            Q(fabric_color__color_name_arb__icontains=search_query) |
            Q(reference_order__icontains=search_query)
        )

    # Apply transaction type filter
    if transaction_type_filter:
        transactions = transactions.filter(transaction_type=transaction_type_filter)

    # Apply fabric filter
    if fabric_filter:
        transactions = transactions.filter(fabric_color_id=fabric_filter)

    # Statistics
    total_transactions = InventoryTransaction.objects.count()
    low_stock_count = FabricColor.objects.filter(quantity__lt=10).count()
    out_of_stock_count = FabricColor.objects.filter(quantity=0).count()

    context = {
        'fabrics': fabrics,
        'transactions': transactions[:50],  # Limit to 50 recent transactions
        'search_query': search_query,
        'transaction_type_filter': transaction_type_filter,
        'fabric_filter': fabric_filter,
        'total_transactions': total_transactions,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'transaction_types': ['ORDER', 'CANCEL', 'RESTOCK', 'ADJUSTMENT'],
    }

    return render(request, 'dashboard/inventory.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def add_stock(request):
    """Add stock to a fabric color (restock or adjustment)"""
    from Design.models import FabricColor, InventoryTransaction

    try:
        fabric_id = request.POST.get('fabric_id')
        quantity = int(request.POST.get('quantity', 0))
        transaction_type = request.POST.get('transaction_type', 'RESTOCK')
        notes = request.POST.get('notes', '')

        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0')
            return redirect('/dashboard/inventory/')

        fabric = FabricColor.objects.get(id=fabric_id)
        quantity_before = fabric.quantity
        quantity_after = quantity_before + quantity

        # Create transaction
        InventoryTransaction.objects.create(
            fabric_color=fabric,
            transaction_type=transaction_type,
            quantity_change=quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            notes=notes,
            created_by=request.user
        )

        # Update stock
        fabric.quantity = quantity_after
        fabric.save()

        messages.success(request, f'Added {quantity} units to {fabric.color_name_eng}. New stock: {quantity_after}')
    except FabricColor.DoesNotExist:
        messages.error(request, 'Fabric not found')
    except Exception as e:
        messages.error(request, f'Error adding stock: {str(e)}')

    return redirect('/dashboard/inventory/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def reduce_stock(request):
    """Reduce stock from a fabric color (adjustment)"""
    from Design.models import FabricColor, InventoryTransaction

    try:
        fabric_id = request.POST.get('fabric_id')
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')

        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0')
            return redirect('/dashboard/inventory/')

        fabric = FabricColor.objects.get(id=fabric_id)
        quantity_before = fabric.quantity

        if quantity > quantity_before:
            messages.error(request, f'Cannot reduce {quantity} units. Current stock is only {quantity_before}')
            return redirect('/dashboard/inventory/')

        quantity_after = quantity_before - quantity

        # Create transaction
        InventoryTransaction.objects.create(
            fabric_color=fabric,
            transaction_type='ADJUSTMENT',
            quantity_change=-quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            notes=notes,
            created_by=request.user
        )

        # Update stock
        fabric.quantity = quantity_after
        fabric.save()

        messages.success(request, f'Reduced {quantity} units from {fabric.color_name_eng}. New stock: {quantity_after}')
    except FabricColor.DoesNotExist:
        messages.error(request, 'Fabric not found')
    except Exception as e:
        messages.error(request, f'Error reducing stock: {str(e)}')

    return redirect('/dashboard/inventory/')


# ==================== USER UPDATE ====================

@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def update_user(request, user_id):
    """Update user information"""
    from User.models import Profile

    try:
        user = User.objects.get(id=user_id)

        # Update user fields
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.is_active = 'is_active' in request.POST
        user.is_staff = 'is_staff' in request.POST
        user.is_superuser = 'is_superuser' in request.POST

        user.save()

        # Update profile fields
        try:
            profile = user.profile
            profile.full_name = request.POST.get('profile_full_name', '')
            profile.phone_number = request.POST.get('profile_phone_number', '')
            profile.premission = request.POST.get('profile_permission', 'User')
            profile.save()
        except Profile.DoesNotExist:
            # Create profile if it doesn't exist
            Profile.objects.create(
                user=user,
                full_name=request.POST.get('profile_full_name', ''),
                phone_number=request.POST.get('profile_phone_number', ''),
                premission=request.POST.get('profile_permission', 'User')
            )

        messages.success(request, f'User {user.username} updated successfully')

    except User.DoesNotExist:
        messages.error(request, 'User not found')
    except Exception as e:
        messages.error(request, f'Error updating user: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', '/dashboard/users/'))


# ==================== FORCE LOGOUT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def force_logout_user(request, user_id):
    """Force logout a specific user by clearing their FCM tokens and JWT refresh tokens"""
    try:
        from User.models import Profile

        user = User.objects.get(id=user_id)

        # Add user to force logout table - will trigger 401 on next API request
        try:
            from User.models import ForceLogoutUser
            ForceLogoutUser.add_user(user, reason="Force logout from admin dashboard")
        except ImportError:
            pass  # Model not available yet (migration pending)

        # Clear FCM token to stop push notifications
        try:
            profile = user.profile
            profile.fcm_token = None
            profile.save()
        except Profile.DoesNotExist:
            pass

        # Try to delete JWT tokens if token blacklist is enabled
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
            OutstandingToken.objects.filter(user=user).delete()
        except Exception:
            # Token blacklist might not be installed, that's okay
            pass

        messages.success(request, f'Successfully forced logout for user: {user.username}. They will be logged out on their next API request.')

    except User.DoesNotExist:
        messages.error(request, 'User not found')
    except Exception as e:
        messages.error(request, f'Error forcing logout: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', '/dashboard/users/'))


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def force_logout_all_users(request):
    """Force logout ALL users (except current user) by clearing their FCM tokens and JWT refresh tokens"""
    try:
        from User.models import Profile

        # Get current user to exclude them
        current_user = request.user

        # Add all users (except current) to force logout table
        try:
            from User.models import ForceLogoutUser
            users_to_logout = User.objects.exclude(id=current_user.id)
            logout_count = 0
            for user in users_to_logout:
                ForceLogoutUser.add_user(user, reason="Force logout all users from admin dashboard")
                logout_count += 1
        except ImportError:
            logout_count = 0  # Model not available yet (migration pending)

        # Clear FCM tokens for all users except current user
        Profile.objects.exclude(user=current_user).update(fcm_token=None)

        # Try to delete JWT tokens if token blacklist is enabled
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
            OutstandingToken.objects.exclude(user=current_user).delete()
        except Exception:
            # Token blacklist might not be installed, that's okay
            pass

        messages.success(request, f'Successfully forced logout for ALL users! {logout_count} users will be logged out on their next API request.')

    except Exception as e:
        messages.error(request, f'Error forcing logout all users: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', '/dashboard/users/'))


# ==================== ADDRESS UPDATE ====================

@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def update_address(request, address_id):
    """Update address information"""
    from User.models import Address

    try:
        address = Address.objects.get(id=address_id)

        # Update address fields
        address.full_name = request.POST.get('full_name', '')
        address.phone_number = request.POST.get('phone_number', '')
        address.address_type = request.POST.get('address_type', 'home')
        address.custom_label = request.POST.get('custom_label', '')
        address.governorate = request.POST.get('governorate', '')
        address.area = request.POST.get('area', '')
        address.block = request.POST.get('block', '')
        address.street = request.POST.get('street', '')
        address.building = request.POST.get('building', '')
        address.apartment = request.POST.get('apartment', '')
        address.floor = request.POST.get('floor', '')
        address.full_address = request.POST.get('full_address', '')
        address.latitude = request.POST.get('latitude') or None
        address.longitude = request.POST.get('longitude') or None
        address.isDefault = 'isDefault' in request.POST

        address.save()

        messages.success(request, f'Address for {address.full_name} updated successfully')

    except Address.DoesNotExist:
        messages.error(request, 'Address not found')
    except Exception as e:
        messages.error(request, f'Error updating address: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', '/dashboard/addresses/'))


# ==================== DELIVERY SETTINGS ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def delivery_settings_view(request):
    """Display and manage delivery settings"""
    from Purchase.models import DeliverySettings

    # Get active delivery settings or create default if none exists
    settings = DeliverySettings.objects.filter(is_active=True).first()

    if not settings:
        # Create default settings if none exist
        settings = DeliverySettings.objects.create(
            delivery_days=5,
            delivery_cost=Decimal('2.000'),
            whatsapp_support='+96500000000',
            is_active=True
        )

    context = {
        'settings': settings,
    }

    return render(request, 'dashboard/delivery_settings.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_delivery_settings(request):
    """Update delivery settings"""
    from Purchase.models import DeliverySettings

    try:
        # Get active settings or create new
        settings = DeliverySettings.objects.filter(is_active=True).first()

        if not settings:
            settings = DeliverySettings()

        # Update fields
        settings.delivery_days = int(request.POST.get('delivery_days', 5))
        settings.delivery_cost = Decimal(request.POST.get('delivery_cost', '2.000'))
        settings.whatsapp_support = request.POST.get('whatsapp_support', '+96500000000')
        settings.is_active = True

        settings.save()

        messages.success(request, 'Delivery settings updated successfully!')

    except Exception as e:
        messages.error(request, f'Error updating delivery settings: {str(e)}')

    return redirect('/dashboard/delivery-settings/')


# ==================== ABOUT US MANAGEMENT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def about_view(request):
    """Display and manage About Us content"""
    from Purchase.models import AboutUs

    # Get or create AboutUs instance
    about_us = AboutUs.objects.first()

    if not about_us:
        about_us = AboutUs.objects.create(
            title_en='About Us',
            title_ar='من نحن',
            content_en='',
            content_ar='',
            is_active=True
        )

    context = {
        'about_us': about_us,
    }

    return render(request, 'dashboard/about.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_about(request):
    """Update About Us content"""
    from Purchase.models import AboutUs

    try:
        about_us = AboutUs.objects.first()

        if not about_us:
            about_us = AboutUs()

        about_us.title_en = request.POST.get('title_en', 'About Us')
        about_us.title_ar = request.POST.get('title_ar', 'من نحن')
        about_us.content_en = request.POST.get('content_en', '')
        about_us.content_ar = request.POST.get('content_ar', '')
        about_us.is_active = 'is_active' in request.POST
        about_us.save()

        messages.success(request, 'About Us content updated successfully!')

    except Exception as e:
        messages.error(request, f'Error updating About Us: {str(e)}')

    return redirect('/dashboard/about/')


# ==================== TERMS AND CONDITIONS MANAGEMENT ====================

@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
def terms_view(request):
    """Display and manage Terms and Conditions content"""
    from Purchase.models import TermsAndConditions

    # Get or create TermsAndConditions instance
    terms = TermsAndConditions.objects.first()

    if not terms:
        terms = TermsAndConditions.objects.create(
            title_en='Terms and Conditions',
            title_ar='الشروط والأحكام',
            content_en='',
            content_ar='',
            is_active=True
        )

    context = {
        'terms': terms,
    }

    return render(request, 'dashboard/terms.html', context)


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_terms(request):
    """Update Terms and Conditions content"""
    from Purchase.models import TermsAndConditions

    try:
        terms = TermsAndConditions.objects.first()

        if not terms:
            terms = TermsAndConditions()

        terms.title_en = request.POST.get('title_en', 'Terms and Conditions')
        terms.title_ar = request.POST.get('title_ar', 'الشروط والأحكام')
        terms.content_en = request.POST.get('content_en', '')
        terms.content_ar = request.POST.get('content_ar', '')
        terms.is_active = 'is_active' in request.POST
        terms.save()

        messages.success(request, 'Terms and Conditions updated successfully!')

    except Exception as e:
        messages.error(request, f'Error updating Terms and Conditions: {str(e)}')

    return redirect('/dashboard/terms/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def create_about_section(request):
    """Create a new About section"""
    from Purchase.models import AboutUs, AboutSection

    try:
        about_us = AboutUs.objects.first()

        if not about_us:
            about_us = AboutUs.objects.create(title_en='About Us', title_ar='من نحن')

        section_type = request.POST.get('section_type')
        title_en = request.POST.get('title_en')
        title_ar = request.POST.get('title_ar')
        content_en = request.POST.get('content_en', '')
        content_ar = request.POST.get('content_ar', '')
        order = int(request.POST.get('order', 0))

        AboutSection.objects.create(
            about_us=about_us,
            section_type=section_type,
            title_en=title_en,
            title_ar=title_ar,
            content_en=content_en,
            content_ar=content_ar,
            order=order
        )

        messages.success(request, f'Section "{title_en}" created successfully!')

    except Exception as e:
        messages.error(request, f'Error creating section: {str(e)}')

    return redirect('/dashboard/about/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_about_section(request, section_id):
    """Update an About section"""
    from Purchase.models import AboutSection

    try:
        section = AboutSection.objects.get(id=section_id)

        section.title_en = request.POST.get('title_en')
        section.title_ar = request.POST.get('title_ar')
        section.content_en = request.POST.get('content_en', '')
        section.content_ar = request.POST.get('content_ar', '')
        section.order = int(request.POST.get('order', 0))
        section.save()

        messages.success(request, f'Section "{section.title_en}" updated successfully!')

    except AboutSection.DoesNotExist:
        messages.error(request, 'Section not found')
    except Exception as e:
        messages.error(request, f'Error updating section: {str(e)}')

    return redirect('/dashboard/about/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def delete_about_section(request, section_id):
    """Delete an About section"""
    from Purchase.models import AboutSection

    try:
        section = AboutSection.objects.get(id=section_id)
        title = section.title_en
        section.delete()
        messages.success(request, f'Section "{title}" deleted successfully!')

    except AboutSection.DoesNotExist:
        messages.error(request, 'Section not found')
    except Exception as e:
        messages.error(request, f'Error deleting section: {str(e)}')

    return redirect('/dashboard/about/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def create_about_value(request):
    """Create a new About value"""
    from Purchase.models import AboutValue, AboutSection

    try:
        section_id = request.POST.get('section_id')
        section = AboutSection.objects.get(id=section_id)

        AboutValue.objects.create(
            section=section,
            title_en=request.POST.get('title_en'),
            title_ar=request.POST.get('title_ar'),
            description_en=request.POST.get('description_en'),
            description_ar=request.POST.get('description_ar'),
            order=int(request.POST.get('order', 0))
        )

        messages.success(request, 'Value created successfully!')

    except AboutSection.DoesNotExist:
        messages.error(request, 'Section not found')
    except Exception as e:
        messages.error(request, f'Error creating value: {str(e)}')

    return redirect('/dashboard/about/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def update_about_value(request, value_id):
    """Update an About value"""
    from Purchase.models import AboutValue

    try:
        value = AboutValue.objects.get(id=value_id)

        value.title_en = request.POST.get('title_en')
        value.title_ar = request.POST.get('title_ar')
        value.description_en = request.POST.get('description_en')
        value.description_ar = request.POST.get('description_ar')
        value.order = int(request.POST.get('order', 0))
        value.save()

        messages.success(request, f'Value "{value.title_en}" updated successfully!')

    except AboutValue.DoesNotExist:
        messages.error(request, 'Value not found')
    except Exception as e:
        messages.error(request, f'Error updating value: {str(e)}')

    return redirect('/dashboard/about/')


@login_required(login_url='/dashboard/login/')
@user_passes_test(is_staff_user, login_url='/dashboard/login/')
@require_http_methods(["POST"])
def delete_about_value(request, value_id):
    """Delete an About value"""
    from Purchase.models import AboutValue

    try:
        value = AboutValue.objects.get(id=value_id)
        title = value.title_en
        value.delete()
        messages.success(request, f'Value "{title}" deleted successfully!')

    except AboutValue.DoesNotExist:
        messages.error(request, 'Value not found')
    except Exception as e:
        messages.error(request, f'Error deleting value: {str(e)}')

    return redirect('/dashboard/about/')
