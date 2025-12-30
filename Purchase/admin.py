from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from django import forms
from .models import Purchase, Item, DeliverySettings, Payment, CancellationRequest, AboutUs, TermsAndConditions
from User.models import Address


class PurchaseAdminForm(forms.ModelForm):
    """Custom form for Purchase admin to filter addresses by user"""

    class Meta:
        model = Purchase
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter addresses by the order's user (only for existing orders with a user)
        if self.instance and self.instance.pk and self.instance.user:
            queryset = Address.objects.filter(
                user=self.instance.user
            ).order_by('-isDefault', '-created_at')

            self.fields['selected_address'].queryset = queryset

            # Show helpful info in dropdown if no addresses
            if not queryset.exists():
                self.fields['selected_address'].help_text = f"User '{self.instance.user.username}' has no saved addresses. They need to add an address first."
            else:
                self.fields['selected_address'].help_text = f"Select from {self.instance.user.username}'s saved addresses"
        else:
            # For new orders or orders without user
            self.fields['selected_address'].queryset = Address.objects.none()
            if not self.instance.pk:
                self.fields['selected_address'].help_text = "Save the order first, then you can select an address"
            elif not self.instance.user:
                self.fields['selected_address'].help_text = "No user assigned to this order"


class ItemInline(admin.TabularInline):
    """Inline model to display order items within Purchase admin"""
    model = Item
    extra = 0
    readonly_fields = ['user_design', 'selected_size', 'product_name', 'category', 'unit_price', 'net_amount', 'quantity', 'discount_percentage', 'product_size', 'cover']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Admin configuration for Purchase (Order) model"""
    form = PurchaseAdminForm

    list_display = [
        'invoice_number',
        'user',
        'full_name',
        'phone_number',
        'total_price',
        'status',
        'payment_option',
        'is_cash',
        'is_pick_up',
        'timestamp'
    ]
    list_filter = ['status', 'payment_option', 'is_cash', 'is_pick_up', 'timestamp']
    search_fields = ['invoice_number', 'full_name', 'email', 'phone_number', 'user__username']
    readonly_fields = [
        'invoice_number',
        'timestamp',
        'user',
        'selected_address_display',
        # Address fields are readonly - admin selects from user's saved addresses
        'address_name',
        'Area',
        'block',
        'street',
        'house',
        'apartment',
        'floor',
        'longitude',
        'latitude',
        'coupon_code',
        'discount_amount',
        'delivery_fee',
    ]
    ordering = ['-timestamp']

    inlines = [ItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('invoice_number', 'user', 'status', 'timestamp')
        }),
        ('Customer Details', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Shipping Address', {
            'fields': (
                'selected_address',
                'selected_address_display',
            ),
            'description': '<strong>Select from user\'s saved addresses (Home/Work/etc.).</strong><br>After selecting, save the order to auto-populate address fields. The selected address details will be shown below.'
        }),
        ('Address Details (Auto-populated)', {
            'fields': (
                'address_name',
                'Area',
                'block',
                'street',
                'house',
                'apartment',
                'floor',
                'longitude',
                'latitude'
            ),
            'classes': ('collapse',),
            'description': 'These fields are automatically populated from the selected address above. They are readonly.'
        }),
        ('Payment & Delivery', {
            'fields': ('payment_option', 'total_price', 'coupon_code', 'discount_amount', 'delivery_fee', 'is_cash', 'is_pick_up')
        }),
        ('External Integration', {
            'fields': ('asap_order_id',),
            'classes': ('collapse',)
        }),
    )

    def selected_address_display(self, obj):
        """Display selected address details in a formatted way"""
        if not obj.selected_address:
            return "No address selected"

        address = obj.selected_address
        html = f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
            <p style="margin: 0 0 10px 0;"><strong style="color: #28a745;">Selected Address:</strong> {address.get_address_type_display()}</p>
            <p style="margin: 5px 0;"><strong>Area:</strong> {address.area or 'N/A'}</p>
            <p style="margin: 5px 0;"><strong>Block:</strong> {address.block or 'N/A'}, <strong>Street:</strong> {address.street or 'N/A'}</p>
            <p style="margin: 5px 0;"><strong>Building:</strong> {address.building or 'N/A'}, <strong>Apartment:</strong> {address.apartment or 'N/A'}, <strong>Floor:</strong> {address.floor or 'N/A'}</p>
            <p style="margin: 5px 0;"><strong>Contact:</strong> {address.full_name} - {address.phone_number}</p>
        </div>
        """
        return mark_safe(html)
    selected_address_display.short_description = 'Currently Selected Address'

    def get_form(self, request, obj=None, **kwargs):
        """Auto-match address from existing order fields if not set"""
        if obj and obj.user and not obj.selected_address and obj.Area:
            # Try to find matching address from user's saved addresses
            matching_address = Address.objects.filter(
                user=obj.user,
                area=obj.Area,
                block=obj.block,
                street=obj.street,
                building=obj.house
            ).first()

            if matching_address:
                # Auto-set the selected_address
                obj.selected_address = matching_address
                obj.save(update_fields=['selected_address'])
                messages.info(request, f'Automatically matched address: {matching_address}')

        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize the address dropdown to show formatted labels"""
        if db_field.name == "selected_address":
            # Get the object being edited
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    purchase = Purchase.objects.get(pk=obj_id)
                    if purchase.user:
                        kwargs["queryset"] = Address.objects.filter(
                            user=purchase.user
                        ).order_by('-isDefault', '-created_at')
                except Purchase.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Auto-populate address fields when admin selects an address"""
        if obj.selected_address:
            # Copy address details from selected_address to order fields
            address = obj.selected_address
            obj.address_name = address.get_address_type_display()
            obj.Area = address.area
            obj.block = address.block
            obj.street = address.street
            obj.house = address.building
            obj.apartment = address.apartment
            obj.floor = address.floor
            obj.longitude = str(address.longitude) if address.longitude else ''
            obj.latitude = str(address.latitude) if address.latitude else ''

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of completed orders
        if obj and obj.status == 'Complete':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin configuration for Item (Order Item) model"""
    list_display = [
        'invoice',
        'product_name',
        'category',
        'user_design',
        'selected_size',
        'unit_price',
        'quantity',
        'discount_percentage',
        'net_amount',
        'created_date'
    ]
    list_filter = ['created_date', 'category', 'discount_percentage']
    search_fields = ['product_name', 'invoice__invoice_number', 'invoice__full_name', 'category']
    readonly_fields = ['user_design', 'selected_size', 'design_details_display', 'size_details_display', 'created_date']
    ordering = ['-created_date']

    def design_details_display(self, obj):
        """Display design details in a readable format"""
        if not obj.design_details:
            return "No design details"

        details = obj.design_details
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background-color: #f0f0f0;'><th style='padding: 8px; border: 1px solid #ddd;'>Component</th><th style='padding: 8px; border: 1px solid #ddd;'>Price (KWD)</th></tr>"

        components = [
            ('Fabric', 'fabric_price'),
            ('Collar', 'collar_price'),
            ('Sleeve Left', 'sleeve_left_price'),
            ('Sleeve Right', 'sleeve_right_price'),
            ('Pocket', 'pocket_price'),
            ('Button', 'button_price'),
            ('Button Strip', 'button_strip_price'),
            ('Body', 'body_price'),
        ]

        for name, key in components:
            value = details.get(key, 0)
            if value and float(value) > 0:
                html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{name}</td><td style='padding: 8px; border: 1px solid #ddd;'>{value}</td></tr>"

        total = details.get('total_price', 0)
        html += f"<tr style='background-color: #e8f4f8; font-weight: bold;'><td style='padding: 8px; border: 1px solid #ddd;'>Total</td><td style='padding: 8px; border: 1px solid #ddd;'>{total}</td></tr>"
        html += "</table>"

        return mark_safe(html)
    design_details_display.short_description = 'Design Details'

    def size_details_display(self, obj):
        """Display size/measurement details in a readable format"""
        if not obj.size_details:
            return "No size details"

        details = obj.size_details
        measurement_type = details.get('measurement_type', 'N/A')

        html = f"<p style='font-weight: bold; color: #0066cc;'>Measurement Type: {measurement_type.upper()}</p>"

        if measurement_type == 'custom':
            html += "<table style='width: 100%; border-collapse: collapse;'>"
            html += "<tr style='background-color: #f0f0f0;'><th style='padding: 8px; border: 1px solid #ddd;'>Measurement</th><th style='padding: 8px; border: 1px solid #ddd;'>Value (cm)</th></tr>"

            measurements = [
                ('Front Height', 'custom_front_height'),
                ('Back Height', 'custom_back_height'),
                ('Around Neck', 'custom_neck'),
                ('Around Legs', 'custom_around_legs'),
                ('Full Chest', 'custom_full_chest'),
                ('Half Chest', 'custom_half_chest'),
                ('Full Belly', 'custom_full_belly'),
                ('Half Belly', 'custom_half_belly'),
                ('Neck to Belly', 'custom_neck_to_belly'),
                ('Neck to Pocket', 'custom_neck_to_pocket'),
                ('Shoulder Width', 'custom_shoulder_width'),
                ('Arm Tall', 'custom_arm_tall'),
                ('Arm Width 1', 'custom_arm_width_1'),
                ('Arm Width 2', 'custom_arm_width_2'),
                ('Arm Width 3', 'custom_arm_width_3'),
                ('Arm Width 4', 'custom_arm_width_4'),
            ]

            for name, key in measurements:
                value = details.get(key, '')
                if value:
                    html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{name}</td><td style='padding: 8px; border: 1px solid #ddd;'>{value}</td></tr>"

            html += "</table>"
        else:
            # Default measurement - show size name
            size_name = details.get('size_name', 'N/A')
            html += f"<p><strong>Size:</strong> {size_name}</p>"

        return mark_safe(html)
    size_details_display.short_description = 'Size/Measurement Details'

    fieldsets = (
        ('Order Information', {
            'fields': ('invoice', 'created_date')
        }),
        ('Design Details (Legacy)', {
            'fields': ('user_design', 'selected_size'),
            'description': 'Legacy fields - for old orders with UserDesign objects',
            'classes': ('collapse',)
        }),
        ('Design Components', {
            'fields': ('design_details_display',),
            'description': 'Design component breakdown showing fabric, collar, buttons, etc. with prices'
        }),
        ('Measurements', {
            'fields': ('size_details_display',),
            'description': 'Custom measurements or selected size information'
        }),
        ('Product Details', {
            'fields': (
                'product_name',
                'category',
                'product_code',
                'product_id',
                'product_size',
                'cover'
            )
        }),
        ('Pricing', {
            'fields': ('unit_price', 'quantity', 'discount', 'discount_percentage', 'net_amount')
        }),
    )


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    """Admin configuration for Delivery Settings"""
    list_display = ['id', 'delivery_days', 'delivery_cost', 'whatsapp_support', 'is_active', 'updated_at']
    list_filter = ['is_active']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Delivery Configuration', {
            'fields': ('delivery_days', 'delivery_cost'),
            'description': 'Configure delivery time and cost displayed in cart screen'
        }),
        ('Support Configuration', {
            'fields': ('whatsapp_support',),
            'description': 'WhatsApp support number with country code (e.g., +96500000000)'
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Only one settings record should be active at a time'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of active settings
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment (Payzah) model"""
    list_display = [
        'track_id',
        'user',
        'purchase',
        'amount',
        'currency',
        'status',
        'verified_with_gateway',
        'created_at'
    ]
    list_filter = ['status', 'currency', 'verified_with_gateway', 'created_at']
    search_fields = [
        'track_id',
        'payzah_payment_id',
        'payzah_reference_code',
        'knet_payment_id',
        'transaction_number',
        'user__username',
        'purchase__invoice_number'
    ]
    readonly_fields = [
        'track_id',
        'payzah_payment_id',
        'user',
        'purchase',
        'idempotency_key',
        'initiated_at',
        'completed_at',
        'created_at',
        'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Payment Information', {
            'fields': ('track_id', 'payzah_payment_id', 'status', 'amount', 'currency')
        }),
        ('Relationships', {
            'fields': ('user', 'purchase')
        }),
        ('Payzah Response Details', {
            'fields': (
                'payzah_reference_code',
                'knet_payment_id',
                'transaction_number',
                'payment_date',
                'payment_status_raw'
            ),
            'classes': ('collapse',)
        }),
        ('User Defined Fields', {
            'fields': ('udf1', 'udf2', 'udf3', 'udf4', 'udf5'),
            'classes': ('collapse',)
        }),
        ('URLs', {
            'fields': ('redirect_url', 'success_url', 'error_url'),
            'classes': ('collapse',)
        }),
        ('Security & Verification', {
            'fields': (
                'idempotency_key',
                'verified_with_gateway',
                'gateway_verification_attempts'
            )
        }),
        ('Metadata', {
            'fields': ('user_agent', 'ip_address', 'initiated_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of captured payments
        if obj and obj.status == 'captured':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    """Admin configuration for Cancellation Request model"""
    list_display = [
        'id',
        'order',
        'order_status',
        'user',
        'status',
        'needs_action',
        'created_at',
        'processed_by',
        'processed_at'
    ]
    list_filter = ['status', 'created_at', 'processed_at']
    search_fields = ['order__invoice_number', 'user__username', 'reason']
    readonly_fields = ['order', 'user', 'reason', 'created_at', 'updated_at']
    ordering = ['-created_at']
    actions = ['cancel_approved_orders']

    fieldsets = (
        ('Request Information', {
            'fields': ('order', 'user', 'reason', 'status', 'created_at')
        }),
        ('Admin Processing', {
            'fields': ('admin_notes', 'processed_by', 'processed_at', 'updated_at'),
            'description': '''
                <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    <strong>⚠️ Important:</strong> When you approve a cancellation request, the order will be <strong>automatically cancelled</strong> and inventory will be restored.
                </div>

                <div style="background-color: #d1ecf1; border: 1px solid #0c5460; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    <strong>Manual Action:</strong> If an approved request shows "⚠️ ACTION NEEDED", select it and use the "Cancel orders for approved requests" action from the dropdown menu.
                </div>

                <strong>Suggested messages based on status:</strong><br><br>

                <strong>For APPROVED status:</strong><br>
                • "طلب الإلغاء مقبول. سيتم إلغاء الطلب ومعالجة الاسترداد." (Arabic)<br>
                • "Cancellation approved. Order will be cancelled and refund processed." (English)<br>
                • "تمت الموافقة على طلبك. سيتم إرجاع المبلغ خلال 3-5 أيام عمل." (Arabic)<br>
                • "Request approved. Refund will be processed within 3-5 business days." (English)<br><br>

                <strong>For REJECTED status (Working):</strong><br>
                • "عذراً، الطلب قيد التنفيذ حالياً ولا يمكن إلغاؤه." (Arabic)<br>
                • "Sorry, order is currently in production and cannot be cancelled." (English)<br>
                • "الطلب في مرحلة متقدمة من التنفيذ. لا يمكن الإلغاء." (Arabic)<br>
                • "Order is in advanced production stage. Cancellation not possible." (English)<br><br>

                <strong>For REJECTED status (Shipping):</strong><br>
                • "عذراً، الطلب في طريقه للتوصيل. لا يمكن الإلغاء الآن." (Arabic)<br>
                • "Sorry, order is out for delivery. Cannot cancel now." (English)<br>
                • "الطلب جاهز للتسليم قريباً. الإلغاء غير ممكن." (Arabic)<br>
                • "Order will be delivered shortly. Cancellation not possible." (English)
            '''
        }),
    )

    def order_status(self, obj):
        """Display the current status of the order with color coding"""
        status = obj.order.status

        # Color code based on status
        if status == 'Cancelled':
            color = '#dc3545'  # Red
        elif status in ['Working', 'Shipping']:
            color = '#ffc107'  # Yellow
        elif status == 'Delivered':
            color = '#28a745'  # Green
        else:
            color = '#6c757d'  # Gray

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    order_status.short_description = 'Order Status'

    def needs_action(self, obj):
        """Show warning if approved request hasn't cancelled the order"""
        if obj.status == 'approved' and obj.order.status != 'Cancelled':
            return mark_safe(
                '<span style="color: #dc3545; font-weight: bold;">⚠️ ACTION NEEDED</span>'
            )
        return '✓'
    needs_action.short_description = 'Status Check'

    def save_model(self, request, obj, form, change):
        """Automatically set processed_by and processed_at when status changes, and cancel order if approved"""
        if change:  # Only for updates, not new objects
            # Get the original object to compare
            original = CancellationRequest.objects.get(pk=obj.pk)

            # If status changed from pending to approved/rejected
            if original.status == 'pending' and obj.status in ['approved', 'rejected']:
                obj.processed_by = request.user
                obj.processed_at = timezone.now()

                # If approved, automatically cancel the order
                if obj.status == 'approved':
                    from .utils import restore_inventory
                    order = obj.order

                    # Restore inventory for all items
                    for item in order.items.all():
                        if item.user_design:
                            restore_inventory(item.user_design, order.invoice_number)

                    # Cancel the order
                    order.status = 'Cancelled'
                    order.cancelled_by = 'admin'
                    order.cancellation_reason = obj.reason
                    order.cancelled_at = timezone.now()
                    order.save()

                    messages.success(request, f'✅ Cancellation approved! Order {order.invoice_number} has been cancelled and inventory restored.')
                    print(f"✅ Order {order.invoice_number} cancelled successfully. Status: {order.status}")
                elif obj.status == 'rejected':
                    messages.info(request, f'Cancellation request rejected. Order {obj.order.invoice_number} remains active.')

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Override delete to show better error message for processed requests"""
        if obj.status in ['approved', 'rejected']:
            messages.error(
                request,
                f'Cannot delete {obj.status} cancellation request (Order: {obj.order.invoice_number}). '
                f'Only pending requests can be deleted to maintain audit trail.'
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Override bulk delete to handle processed requests gracefully"""
        # Separate pending and processed requests
        pending_requests = queryset.filter(status='pending')
        processed_requests = queryset.filter(status__in=['approved', 'rejected'])

        # Delete only pending requests
        pending_count = pending_requests.count()
        processed_count = processed_requests.count()

        if pending_count > 0:
            pending_requests.delete()
            messages.success(request, f'{pending_count} pending cancellation request(s) deleted successfully.')

        if processed_count > 0:
            messages.warning(
                request,
                f'{processed_count} processed cancellation request(s) were skipped. '
                f'Only pending requests can be deleted to maintain audit trail.'
            )

    def has_delete_permission(self, request, obj=None):
        # Allow delete permission in general (we'll handle specific cases in delete_model)
        # This prevents the confusing permission error message
        return super().has_delete_permission(request, obj)

    def cancel_approved_orders(self, request, queryset):
        """Admin action to cancel orders for approved cancellation requests"""
        from .utils import restore_inventory

        # Filter only approved requests where order is not yet cancelled
        approved_requests = queryset.filter(status='approved').exclude(order__status='Cancelled')

        cancelled_count = 0
        already_cancelled_count = 0

        for req in approved_requests:
            order = req.order

            # Check if order is already cancelled
            if order.status == 'Cancelled':
                already_cancelled_count += 1
                continue

            # Restore inventory for all items
            for item in order.items.all():
                if item.user_design:
                    restore_inventory(item.user_design, order.invoice_number)

            # Cancel the order
            order.status = 'Cancelled'
            order.cancelled_by = 'admin'
            order.cancellation_reason = req.reason
            order.cancelled_at = timezone.now()
            order.save()

            cancelled_count += 1

        # Show messages
        if cancelled_count > 0:
            messages.success(request, f'✅ Successfully cancelled {cancelled_count} order(s) and restored inventory.')
        if already_cancelled_count > 0:
            messages.info(request, f'ℹ️ {already_cancelled_count} order(s) were already cancelled.')
        if cancelled_count == 0 and already_cancelled_count == 0:
            messages.warning(request, 'No approved cancellation requests with active orders found.')

    cancel_approved_orders.short_description = "Cancel orders for approved requests"


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    """Admin configuration for About Us content"""
    list_display = ['id', 'title_en', 'title_ar', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title_en', 'title_ar', 'content_en', 'content_ar']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('About Us Information', {
            'fields': ('title_en', 'title_ar', 'is_active'),
            'description': '''
                <div style="background-color: #d1ecf1; border: 1px solid #0c5460; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    <strong>ℹ️ How to use:</strong><br>
                    1. Only ONE About Us record should be active at a time<br>
                    2. Edit content in English and Arabic below<br>
                    3. Use the Dashboard at /dashboard/about/ for rich text editing
                </div>
            '''
        }),
        ('Content', {
            'fields': ('content_en', 'content_ar'),
            'description': 'For rich text editing, use the Dashboard at /dashboard/about/'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of active About Us content
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    """Admin configuration for Terms and Conditions content"""
    list_display = ['id', 'title_en', 'title_ar', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title_en', 'title_ar', 'content_en', 'content_ar']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Terms and Conditions Information', {
            'fields': ('title_en', 'title_ar', 'is_active'),
            'description': '''
                <div style="background-color: #d1ecf1; border: 1px solid #0c5460; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    <strong>ℹ️ How to use:</strong><br>
                    1. Only ONE Terms and Conditions record should be active at a time<br>
                    2. Edit content in English and Arabic below<br>
                    3. Use the Dashboard at /dashboard/terms/ for rich text editing
                </div>
            '''
        }),
        ('Content', {
            'fields': ('content_en', 'content_ar'),
            'description': 'For rich text editing, use the Dashboard at /dashboard/terms/'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of active Terms and Conditions content
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)
