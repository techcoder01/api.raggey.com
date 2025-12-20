"""
Dashboard Analytics Views for Admin Panel
Provides KPIs, charts data, and tables for admin dashboard
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Purchase, Item
from Design.models import FabricColor, FabricType, UserDesign
from django.contrib.auth.models import User


class DashboardKPIAPIView(APIView):
    """
    GET: Get dashboard KPIs (Key Performance Indicators)
    Endpoint: /purchase/analytics/kpis/
    Query params: ?period=30 (days, default: 30)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            period_days = int(request.GET.get('period', 30))
            start_date = datetime.now() - timedelta(days=period_days)

            # Total Revenue
            total_revenue = Purchase.objects.filter(
                timestamp__gte=start_date,
                status__in=['Complete', 'Delivering', 'Ready']
            ).aggregate(total=Sum('total_price'))['total'] or Decimal('0.000')

            # Total Orders
            total_orders = Purchase.objects.filter(
                timestamp__gte=start_date
            ).count()

            # Pending Orders
            pending_orders = Purchase.objects.filter(
                status='Pending'
            ).count()

            # Completed Orders
            completed_orders = Purchase.objects.filter(
                timestamp__gte=start_date,
                status='Complete'
            ).count()

            # Active Users (users who placed orders)
            active_users = Purchase.objects.filter(
                timestamp__gte=start_date
            ).values('user').distinct().count()

            # Low Stock Items (quantity <= 5)
            low_stock_count = FabricColor.objects.filter(
                quantity__lte=5
            ).count()

            # Average Order Value
            avg_order_value = Purchase.objects.filter(
                timestamp__gte=start_date,
                status__in=['Complete', 'Delivering', 'Ready']
            ).aggregate(avg=Avg('total_price'))['avg'] or Decimal('0.000')

            # Conversion Rate (completed / total orders)
            conversion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

            return Response({
                'period_days': period_days,
                'kpis': {
                    'total_revenue': float(total_revenue),
                    'total_orders': total_orders,
                    'pending_orders': pending_orders,
                    'completed_orders': completed_orders,
                    'active_users': active_users,
                    'low_stock_items': low_stock_count,
                    'avg_order_value': float(avg_order_value),
                    'conversion_rate': round(conversion_rate, 2)
                }
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch KPIs',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class RevenueTrendAPIView(APIView):
    """
    GET: Get revenue trend data for charts
    Endpoint: /purchase/analytics/revenue-trend/
    Query params: ?period=30 (days, default: 30)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            period_days = int(request.GET.get('period', 30))
            start_date = datetime.now() - timedelta(days=period_days)

            # Group by date
            daily_revenue = Purchase.objects.filter(
                timestamp__gte=start_date,
                status__in=['Complete', 'Delivering', 'Ready']
            ).annotate(
                date=TruncDate('timestamp')
            ).values('date').annotate(
                revenue=Sum('total_price'),
                orders_count=Count('id')
            ).order_by('date')

            data = []
            for item in daily_revenue:
                data.append({
                    'date': item['date'].strftime('%Y-%m-%d'),
                    'revenue': float(item['revenue']),
                    'orders_count': item['orders_count']
                })

            return Response({
                'period_days': period_days,
                'data': data
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch revenue trend',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class OrderStatusDistributionAPIView(APIView):
    """
    GET: Get order status distribution for pie/donut charts
    Endpoint: /purchase/analytics/order-status/
    Query params: ?period=30 (days, default: 30)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            period_days = int(request.GET.get('period', 30))
            start_date = datetime.now() - timedelta(days=period_days)

            status_distribution = Purchase.objects.filter(
                timestamp__gte=start_date
            ).values('status').annotate(
                count=Count('id'),
                revenue=Sum('total_price')
            ).order_by('-count')

            data = []
            for item in status_distribution:
                data.append({
                    'status': item['status'],
                    'count': item['count'],
                    'revenue': float(item['revenue'] or 0)
                })

            return Response({
                'period_days': period_days,
                'data': data
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch order status distribution',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class PopularFabricsAPIView(APIView):
    """
    GET: Get most popular fabric colors used in orders
    Endpoint: /purchase/analytics/popular-fabrics/
    Query params: ?limit=10 (default: 10)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 10))

            # Get most used fabrics from UserDesign linked to orders
            popular_fabrics = UserDesign.objects.filter(
                order_items__isnull=False
            ).values(
                'main_body_fabric_color__id',
                'main_body_fabric_color__color_name_eng',
                'main_body_fabric_color__fabric_type__fabric_name_eng'
            ).annotate(
                usage_count=Count('id')
            ).order_by('-usage_count')[:limit]

            data = []
            for fabric in popular_fabrics:
                if fabric['main_body_fabric_color__id']:
                    data.append({
                        'fabric_color_id': fabric['main_body_fabric_color__id'],
                        'fabric_type': fabric['main_body_fabric_color__fabric_type__fabric_name_eng'],
                        'color_name': fabric['main_body_fabric_color__color_name_eng'],
                        'usage_count': fabric['usage_count']
                    })

            return Response({
                'limit': limit,
                'data': data
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch popular fabrics',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class TopCustomersAPIView(APIView):
    """
    GET: Get top customers by order value
    Endpoint: /purchase/analytics/top-customers/
    Query params: ?limit=10 (default: 10), ?period=90 (days)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 10))
            period_days = int(request.GET.get('period', 90))
            start_date = datetime.now() - timedelta(days=period_days)

            top_customers = Purchase.objects.filter(
                timestamp__gte=start_date,
                status__in=['Complete', 'Delivering', 'Ready']
            ).values(
                'user__id',
                'user__username',
                'user__email',
                'user__first_name',
                'user__last_name'
            ).annotate(
                total_spent=Sum('total_price'),
                order_count=Count('id')
            ).order_by('-total_spent')[:limit]

            data = []
            for customer in top_customers:
                data.append({
                    'user_id': customer['user__id'],
                    'username': customer['user__username'],
                    'email': customer['user__email'] or '',
                    'full_name': f"{customer['user__first_name'] or ''} {customer['user__last_name'] or ''}".strip(),
                    'total_spent': float(customer['total_spent']),
                    'order_count': customer['order_count'],
                    'avg_order_value': float(customer['total_spent'] / customer['order_count'])
                })

            return Response({
                'limit': limit,
                'period_days': period_days,
                'data': data
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch top customers',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class RecentOrdersTableAPIView(APIView):
    """
    GET: Get recent orders for dashboard table
    Endpoint: /purchase/analytics/recent-orders/
    Query params: ?limit=20 (default: 20)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 20))

            recent_orders = Purchase.objects.select_related('user').order_by('-timestamp')[:limit]

            data = []
            for order in recent_orders:
                data.append({
                    'id': order.id,
                    'invoice_number': order.invoice_number,
                    'customer_name': order.full_name,
                    'email': order.email or '',
                    'phone': order.phone_number,
                    'total_price': float(order.total_price),
                    'status': order.status,
                    'payment_method': order.payment_option,
                    'timestamp': order.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'items_count': order.items.count()
                })

            return Response({
                'limit': limit,
                'data': data
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch recent orders',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class InventoryStatusTableAPIView(APIView):
    """
    GET: Get inventory status for all fabric colors
    Endpoint: /purchase/analytics/inventory-status/
    Query params: ?low_stock_threshold=10 (default: 10)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            threshold = int(request.GET.get('low_stock_threshold', 10))

            fabrics = FabricColor.objects.select_related('fabric_type').order_by('quantity')

            data = []
            for fabric in fabrics:
                # Calculate usage (times ordered)
                usage_count = UserDesign.objects.filter(
                    order_items__isnull=False,
                    main_body_fabric_color=fabric
                ).count()

                data.append({
                    'id': fabric.id,
                    'fabric_type': fabric.fabric_type.fabric_name_eng,
                    'color_name': fabric.color_name_eng,
                    'quantity': fabric.quantity,
                    'inStock': fabric.inStock,
                    'status': 'Critical' if fabric.quantity == 0 else ('Low' if fabric.quantity <= threshold else 'Adequate'),
                    'usage_count': usage_count,
                    'price': float(fabric.total_price)
                })

            return Response({
                'threshold': threshold,
                'total_fabrics': len(data),
                'data': data
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch inventory status',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)
