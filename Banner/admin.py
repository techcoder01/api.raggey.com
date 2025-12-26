from django.contrib import admin
from .models import Banner

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)
    list_editable = ('order', 'is_active')
    ordering = ('order', '-created_at')

    fieldsets = (
        ('Banner Information', {
            'fields': ('title', 'order', 'is_active')
        }),
        ('Images', {
            'fields': ('image_en', 'image_ar'),
            'description': 'Upload banner images for English and Arabic languages'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')
