from django.contrib import admin
from django.utils.html import format_html
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name_en', 'coupon_type', 'discount_display',
        'current_uses', 'max_uses', 'is_active_display', 'valid_until'
    ]
    list_filter = ['coupon_type', 'discount_type', 'is_active', 'is_featured', 'created_at']
    search_fields = ['code', 'name_en', 'name_ar', 'description_en', 'description_ar']
    ordering = ['-created_at']
    readonly_fields = ['current_uses', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name_en', 'name_ar', 'description_en', 'description_ar')
        }),
        ('Discount Configuration', {
            'fields': ('coupon_type', 'discount_type', 'discount_value', 'min_order_amount', 'max_discount_amount')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'current_uses', 'max_uses_per_user')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
        ('Card Coupon Display (Optional)', {
            'fields': ('is_featured', 'card_color', 'card_icon'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def discount_display(self, obj):
        """Display formatted discount"""
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}%"
        else:
            return f"{obj.discount_value} KWD"
    discount_display.short_description = 'Discount'

    def is_active_display(self, obj):
        """Display active status with color"""
        is_valid, message = obj.is_valid()
        if is_valid:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ {}</span>',
                message
            )
    is_active_display.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related().prefetch_related('usages')

    actions = ['activate_coupons', 'deactivate_coupons']

    def activate_coupons(self, request, queryset):
        """Bulk activate coupons"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} coupon(s) activated.')
    activate_coupons.short_description = 'Activate selected coupons'

    def deactivate_coupons(self, request, queryset):
        """Bulk deactivate coupons"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} coupon(s) deactivated.')
    deactivate_coupons.short_description = 'Deactivate selected coupons'


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'coupon_code', 'user_id', 'order_id',
        'discount_amount', 'order_amount', 'used_at'
    ]
    list_filter = ['used_at', 'coupon']
    search_fields = ['coupon__code', 'user_id', 'order_id']
    ordering = ['-used_at']
    readonly_fields = ['coupon', 'user_id', 'order_id', 'discount_amount', 'order_amount', 'used_at']

    def coupon_code(self, obj):
        """Display coupon code"""
        return obj.coupon.code
    coupon_code.short_description = 'Coupon Code'

    def has_add_permission(self, request):
        """Disable manual creation of coupon usages"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing of coupon usages"""
        return False

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('coupon')
