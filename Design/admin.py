from django.contrib import admin
from .fabric_notifications import (
    notify_fabric_created,
    notify_fabric_updated,
    notify_fabric_deleted,
    notify_fabric_hidden_changed,
    notify_fabric_color_created,
    notify_fabric_color_updated,
    notify_fabric_color_deleted,
)

from .models import (
    HomePageSelectionCategory,
    FabricType, FabricColor,
    GholaType, SleevesType, PocketType, ButtonType, BodyType,
    UserDesign, InventoryTransaction, DesignScreenshot
)

# Register your models here.
@admin.register(HomePageSelectionCategory)
class HomePageSelectionCategoryAdmin(admin.ModelAdmin):
    list_display = ('main_category_name_eng', 'main_category_name_arb', 'initial_price', 'priority', 'isHidden')
    list_editable = ('priority', 'isHidden')
    search_fields = ('main_category_name_eng', 'main_category_name_arb')

# NEW: Fabric models
@admin.register(FabricType)
class FabricTypeAdmin(admin.ModelAdmin):
    list_display = ('fabric_name_eng', 'fabric_name_arb', 'base_price', 'category_type', 'season', 'priority', 'isHidden')
    list_editable = ('priority',)
    list_filter = ('category_type', 'season', 'isHidden')
    search_fields = ('fabric_name_eng', 'fabric_name_arb')

    def save_model(self, request, obj, form, change):
        """Send FCM notification when fabric is created or updated."""
        is_new = obj.pk is None
        old_is_hidden = None

        # Track isHidden changes for existing fabrics
        if change and 'isHidden' in form.changed_data:
            old_fabric = FabricType.objects.get(pk=obj.pk)
            old_is_hidden = old_fabric.isHidden

        super().save_model(request, obj, form, change)

        # Send appropriate notification
        if is_new:
            notify_fabric_created()
        else:
            # Check if isHidden was changed
            if old_is_hidden is not None and old_is_hidden != obj.isHidden:
                notify_fabric_hidden_changed(obj.id, obj.isHidden)
            else:
                notify_fabric_updated(obj.id)

    def delete_model(self, request, obj):
        """Send FCM notification when fabric is deleted."""
        super().delete_model(request, obj)
        notify_fabric_deleted()

@admin.register(FabricColor)
class FabricColorAdmin(admin.ModelAdmin):
    list_display = ('get_fabric_name', 'color_name_eng', 'color_name_arb', 'hex_color', 'get_total_price', 'quantity', 'priority', 'inStock')
    list_editable = ('priority',)
    list_filter = ('fabric_type', 'inStock')
    search_fields = ('color_name_eng', 'color_name_arb', 'fabric_type__fabric_name_eng')

    def get_fabric_name(self, obj):
        return obj.fabric_type.fabric_name_eng
    get_fabric_name.short_description = 'Fabric Type'

    def get_total_price(self, obj):
        return obj.total_price
    get_total_price.short_description = 'Total Price'

    def save_model(self, request, obj, form, change):
        """Send FCM notification when fabric color is created or updated."""
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new:
            notify_fabric_color_created()
        else:
            notify_fabric_color_updated()

    def delete_model(self, request, obj):
        """Send FCM notification when fabric color is deleted."""
        super().delete_model(request, obj)
        notify_fabric_color_deleted()

# Component models
@admin.register(GholaType)
class GholaTypeAdmin(admin.ModelAdmin):
    list_display = ('ghola_type_name_eng', 'ghola_type_name_arb', 'get_fabric_type', 'get_fabric_color', 'initial_price', 'priority')
    list_editable = ('priority',)
    list_filter = ('fabric_type', 'fabric_color')
    search_fields = ('ghola_type_name_eng', 'ghola_type_name_arb', 'fabric_color__color_name_eng')

    def get_fabric_type(self, obj):
        if obj.fabric_type:
            return f"{obj.fabric_type.fabric_name_eng}"
        return "No Fabric Type"
    get_fabric_type.short_description = 'Fabric Type'

    def get_fabric_color(self, obj):
        if obj.fabric_color:
            return obj.fabric_color.color_name_eng
        return "No Color"
    get_fabric_color.short_description = 'Color'

@admin.register(SleevesType)
class SleevesTypeAdmin(admin.ModelAdmin):
    list_display = ('sleeves_type_name_eng', 'sleeves_type_name_arb', 'get_fabric_type', 'get_fabric_color', 'is_right_side', 'initial_price', 'priority')
    list_editable = ('priority',)
    list_filter = ('is_right_side', 'fabric_type', 'fabric_color')
    search_fields = ('sleeves_type_name_eng', 'sleeves_type_name_arb', 'fabric_color__color_name_eng')

    def get_fabric_type(self, obj):
        if obj.fabric_type:
            return f"{obj.fabric_type.fabric_name_eng}"
        return "No Fabric Type"
    get_fabric_type.short_description = 'Fabric Type'

    def get_fabric_color(self, obj):
        if obj.fabric_color:
            return obj.fabric_color.color_name_eng
        return "No Color"
    get_fabric_color.short_description = 'Color'

@admin.register(PocketType)
class PocketTypeAdmin(admin.ModelAdmin):
    list_display = ('pocket_type_name_eng', 'pocket_type_name_arb', 'get_fabric_type', 'get_fabric_color', 'initial_price', 'priority')
    list_editable = ('priority',)
    list_filter = ('fabric_type', 'fabric_color')
    search_fields = ('pocket_type_name_eng', 'pocket_type_name_arb', 'fabric_color__color_name_eng')

    def get_fabric_type(self, obj):
        if obj.fabric_type:
            return f"{obj.fabric_type.fabric_name_eng}"
        return "No Fabric Type"
    get_fabric_type.short_description = 'Fabric Type'

    def get_fabric_color(self, obj):
        if obj.fabric_color:
            return obj.fabric_color.color_name_eng
        return "No Color"
    get_fabric_color.short_description = 'Color'

@admin.register(ButtonType)
class ButtonTypeAdmin(admin.ModelAdmin):
    list_display = ('button_type_name_eng', 'button_type_name_arb', 'get_fabric_type', 'get_fabric_color', 'initial_price', 'priority', 'inStock')
    list_editable = ('priority',)
    list_filter = ('inStock', 'fabric_type', 'fabric_color')
    search_fields = ('button_type_name_eng', 'button_type_name_arb', 'fabric_color__color_name_eng')

    def get_fabric_type(self, obj):
        if obj.fabric_type:
            return f"{obj.fabric_type.fabric_name_eng}"
        return "No Fabric Type"
    get_fabric_type.short_description = 'Fabric Type'

    def get_fabric_color(self, obj):
        if obj.fabric_color:
            return obj.fabric_color.color_name_eng
        return "No Color"
    get_fabric_color.short_description = 'Color'



@admin.register(BodyType)
class BodyTypeAdmin(admin.ModelAdmin):
    list_display = ('body_type_name_eng', 'body_type_name_arb', 'get_fabric_type', 'get_fabric_color', 'initial_price')
    list_filter = ('fabric_type', 'fabric_color')
    search_fields = ('body_type_name_eng', 'body_type_name_arb', 'fabric_color__color_name_eng')

    def get_fabric_type(self, obj):
        if obj.fabric_type:
            return f"{obj.fabric_type.fabric_name_eng}"
        return "No Fabric Type"
    get_fabric_type.short_description = 'Fabric Type'

    def get_fabric_color(self, obj):
        if obj.fabric_color:
            return obj.fabric_color.color_name_eng
        return "No Color"
    get_fabric_color.short_description = 'Color'

# User design
@admin.register(UserDesign)
class UserDesignAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'design_name', 'get_fabric_color', 'design_Total', 'timestamp')
    list_filter = ('timestamp', 'main_body_fabric_color__fabric_type')
    search_fields = ('user__username', 'design_name')

    def get_fabric_color(self, obj):
        if obj.main_body_fabric_color:
            return f"{obj.main_body_fabric_color.fabric_type.fabric_name_eng} - {obj.main_body_fabric_color.color_name_eng}"
        return "No Fabric Color"
    get_fabric_color.short_description = 'Main Fabric Color'

# Inventory tracking
@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_fabric_color', 'transaction_type', 'quantity_change', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('fabric_color__color_name_eng', 'fabric_color__fabric_type__fabric_name_eng')

    def get_fabric_color(self, obj):
        if obj.fabric_color:
            return f"{obj.fabric_color.fabric_type.fabric_name_eng} - {obj.fabric_color.color_name_eng}"
        return "No Fabric Color"
    get_fabric_color.short_description = 'Fabric Color'


# Design Screenshot caching
@admin.register(DesignScreenshot)
class DesignScreenshotAdmin(admin.ModelAdmin):
    list_display = ('design_hash_short', 'screenshot_url_preview', 'times_reused', 'created_at', 'last_accessed')
    list_filter = ('created_at', 'last_accessed')
    search_fields = ('design_hash', 'fabric_color_id', 'collar_id')
    readonly_fields = ('design_hash', 'times_reused', 'created_at', 'last_accessed')

    def design_hash_short(self, obj):
        return f"{obj.design_hash[:16]}..."
    design_hash_short.short_description = 'Design Hash'

    def screenshot_url_preview(self, obj):
        from django.utils.html import format_html
        if obj.screenshot_url:
            return format_html('<a href="{}" target="_blank">View Screenshot</a>', obj.screenshot_url)
        return "No URL"
    screenshot_url_preview.short_description = 'Screenshot'
