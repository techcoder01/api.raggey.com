from django.contrib import admin
from .models import Address, Profile


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'address_type', 'governorate', 'area', 'phone_number', 'isDefault', 'created_at')
    list_filter = ('address_type', 'isDefault', 'governorate', 'created_at')
    search_fields = ('full_name', 'user__username', 'user__email', 'phone_number', 'governorate', 'area', 'block', 'street')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'phone_number')
        }),
        ('Location Coordinates', {
            'fields': ('longitude', 'latitude', 'full_address')
        }),
        ('Address Details', {
            'fields': ('governorate', 'area', 'block', 'street', 'building', 'apartment', 'floor')
        }),
        ('Address Labeling', {
            'fields': ('address_type', 'custom_label', 'isDefault')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(Profile)
