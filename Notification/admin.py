from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import PromotionalNotification, NotificationLog, CartAbandonmentTracker


@admin.register(PromotionalNotification)
class PromotionalNotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for creating and sending promotional notifications
    Admins can send messages to app users anytime
    """
    list_display = [
        'title',
        'priority_badge',
        'channel_badge',
        'status_badge',
        'sent_count_display',
        'created_at_display',
        'send_button',
    ]
    list_filter = [
        'is_sent',
        'priority',
        'channel',
        'created_at',
    ]
    search_fields = [
        'title',
        'message',
        'promo_code',
    ]
    readonly_fields = [
        'is_sent',
        'sent_at',
        'sent_count',
        'created_at',
        'created_by',
    ]
    fieldsets = (
        ('Notification Content', {
            'fields': ('title', 'message')
        }),
        ('Targeting', {
            'fields': ('send_to_all', 'target_users'),
            'description': 'Choose who should receive this notification'
        }),
        ('Delivery Settings', {
            'fields': ('priority', 'channel'),
        }),
        ('Promotional Details (Optional)', {
            'fields': ('promo_code', 'discount_percentage'),
            'classes': ('collapse',),
        }),
        ('Scheduling (Optional)', {
            'fields': ('scheduled_time',),
            'description': 'Leave blank to send immediately when you click "Send"'
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at', 'sent_count', 'created_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )
    filter_horizontal = ('target_users',)
    actions = ['send_notifications_action']

    def save_model(self, request, obj, form, change):
        """Save model and set created_by to current admin user"""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def priority_badge(self, obj):
        """Display priority as colored badge"""
        colors = {
            'low': '#10B981',      # Green
            'medium': '#F59E0B',   # Orange
            'high': '#EF4444',     # Red
        }
        color = colors.get(obj.priority, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_priority_display().upper()
        )
    priority_badge.short_description = 'Priority'

    def channel_badge(self, obj):
        """Display channel as badge"""
        icons = {
            'push': '🔔',
            'email': '📧',
            'in_app': '📱',
        }
        icon = icons.get(obj.channel, '📬')
        return format_html(
            '<span style="background-color: #3B82F6; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">{} {}</span>',
            icon,
            obj.get_channel_display()
        )
    channel_badge.short_description = 'Channel'

    def status_badge(self, obj):
        """Display status as colored badge"""
        if obj.is_sent:
            return format_html(
                '<span style="background-color: #10B981; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">✅ SENT</span>'
            )
        elif obj.scheduled_time and obj.scheduled_time > timezone.now():
            return format_html(
                '<span style="background-color: #8B5CF6; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">⏰ SCHEDULED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #F59E0B; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">⏳ PENDING</span>'
            )
    status_badge.short_description = 'Status'

    def sent_count_display(self, obj):
        """Display sent count"""
        if obj.is_sent:
            return format_html(
                '<strong style="color: #10B981;">{}</strong> users',
                obj.sent_count
            )
        return '—'
    sent_count_display.short_description = 'Delivered To'

    def created_at_display(self, obj):
        """Display created date"""
        return obj.created_at.strftime('%b %d, %Y %H:%M')
    created_at_display.short_description = 'Created'

    def send_button(self, obj):
        """Display send button for unsent notifications"""
        if not obj.is_sent:
            return format_html(
                '<a class="button" href="/admin/notification/promotionalnotification/{}/send/" '
                'style="background-color: #0B5D35; color: white; padding: 6px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">🚀 Send Now</a>',
                obj.pk
            )
        return '—'
    send_button.short_description = 'Actions'

    def send_notifications_action(self, request, queryset):
        """Admin action to send selected notifications"""
        total_sent = 0
        total_notifications = 0

        for notification in queryset.filter(is_sent=False):
            count = notification.send_notification()
            total_sent += count
            total_notifications += 1

        self.message_user(
            request,
            f'✅ Successfully sent {total_notifications} notifications to {total_sent} users!'
        )
    send_notifications_action.short_description = '🚀 Send selected notifications'


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing notification history
    """
    list_display = [
        'notification_type_badge',
        'user_email',
        'title',
        'priority_badge',
        'channel_badge',
        'status_badge',
        'created_at_display',
    ]
    list_filter = [
        'notification_type',
        'priority',
        'channel',
        'was_sent',
        'created_at',
    ]
    search_fields = [
        'title',
        'body',
        'user__user__email',
        'user__user__first_name',
        'user__user__last_name',
    ]
    readonly_fields = [
        'notification_type',
        'priority',
        'channel',
        'user',
        'title',
        'body',
        'order_id',
        'promotional_notification',
        'was_sent',
        'error_message',
        'created_at',
        'sent_at',
    ]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        """Disable manual creation - logs are auto-generated"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True

    def notification_type_badge(self, obj):
        """Display notification type as badge"""
        colors = {
            'order_placed': '#3B82F6',
            'order_confirmed': '#10B981',
            'order_packed': '#8B5CF6',
            'out_for_delivery': '#F59E0B',
            'order_delivered': '#10B981',
            'order_cancelled': '#EF4444',
            'cart_abandoned': '#F59E0B',
            'promotional': '#EC4899',
            'payment_success': '#10B981',
            'payment_failed': '#EF4444',
        }
        color = colors.get(obj.notification_type, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Type'

    def user_email(self, obj):
        """Display user email"""
        return obj.user.user.email if obj.user.user else 'Unknown'
    user_email.short_description = 'User'

    def priority_badge(self, obj):
        """Display priority as colored badge"""
        colors = {
            'low': '#10B981',
            'medium': '#F59E0B',
            'high': '#EF4444',
        }
        color = colors.get(obj.priority, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 8px; font-size: 10px; font-weight: 600;">{}</span>',
            color,
            obj.get_priority_display().upper()
        )
    priority_badge.short_description = 'Priority'

    def channel_badge(self, obj):
        """Display channel as badge"""
        icons = {
            'push': '🔔',
            'email': '📧',
            'in_app': '📱',
        }
        icon = icons.get(obj.channel, '📬')
        return format_html(
            '<span>{} {}</span>',
            icon,
            obj.get_channel_display()
        )
    channel_badge.short_description = 'Channel'

    def status_badge(self, obj):
        """Display status"""
        if obj.was_sent:
            return format_html(
                '<span style="color: #10B981; font-weight: 600;">✅ Sent</span>'
            )
        return format_html(
            '<span style="color: #EF4444; font-weight: 600;">❌ Failed</span>'
        )
    status_badge.short_description = 'Status'

    def created_at_display(self, obj):
        """Display created date"""
        return obj.created_at.strftime('%b %d, %Y %H:%M')
    created_at_display.short_description = 'Sent At'


@admin.register(CartAbandonmentTracker)
class CartAbandonmentTrackerAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing cart abandonments
    """
    list_display = [
        'user_email',
        'cart_items_count',
        'cart_total_display',
        'cart_age_display',
        'notification_status_badge',
        'conversion_status_badge',
    ]
    list_filter = [
        'notification_sent',
        'order_completed',
        'cart_last_updated',
    ]
    search_fields = [
        'user__user__email',
        'user__user__first_name',
        'user__user__last_name',
    ]
    readonly_fields = [
        'user',
        'cart_items_count',
        'cart_total',
        'cart_last_updated',
        'created_at',
        'notification_sent',
        'notification_sent_at',
        'order_completed',
        'order_completed_at',
    ]
    date_hierarchy = 'cart_last_updated'

    def has_add_permission(self, request):
        """Disable manual creation"""
        return False

    def user_email(self, obj):
        """Display user email"""
        return obj.user.user.email if obj.user.user else 'Unknown'
    user_email.short_description = 'User'

    def cart_total_display(self, obj):
        """Display cart total"""
        return format_html(
            '<strong>{} KWD</strong>',
            obj.cart_total
        )
    cart_total_display.short_description = 'Cart Total'

    def cart_age_display(self, obj):
        """Display how long ago cart was updated"""
        time_diff = timezone.now() - obj.cart_last_updated
        hours = int(time_diff.total_seconds() / 3600)

        if hours < 24:
            return format_html(
                '<span style="color: #6B7280;">{} hours ago</span>',
                hours
            )
        elif hours < 48:
            return format_html(
                '<span style="color: #F59E0B; font-weight: 600;">24+ hours ago</span>'
            )
        else:
            days = int(hours / 24)
            return format_html(
                '<span style="color: #EF4444; font-weight: 600;">{} days ago</span>',
                days
            )
    cart_age_display.short_description = 'Cart Age'

    def notification_status_badge(self, obj):
        """Display notification status"""
        if obj.notification_sent:
            return format_html(
                '<span style="background-color: #10B981; color: white; padding: 3px 8px; border-radius: 8px; font-size: 10px; font-weight: 600;">✅ SENT</span>'
            )
        elif obj.should_send_notification():
            return format_html(
                '<span style="background-color: #F59E0B; color: white; padding: 3px 8px; border-radius: 8px; font-size: 10px; font-weight: 600;">⏰ DUE</span>'
            )
        return format_html(
            '<span style="background-color: #6B7280; color: white; padding: 3px 8px; border-radius: 8px; font-size: 10px; font-weight: 600;">⏳ PENDING</span>'
        )
    notification_status_badge.short_description = 'Notification'

    def conversion_status_badge(self, obj):
        """Display conversion status"""
        if obj.order_completed:
            return format_html(
                '<span style="background-color: #10B981; color: white; padding: 3px 8px; border-radius: 8px; font-size: 10px; font-weight: 600;">🎉 CONVERTED</span>'
            )
        return format_html(
            '<span style="background-color: #6B7280; color: white; padding: 3px 8px; border-radius: 8px; font-size: 10px; font-weight: 600;">⏳ ABANDONED</span>'
        )
    conversion_status_badge.short_description = 'Conversion'
