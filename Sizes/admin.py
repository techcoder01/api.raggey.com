from django.contrib import admin
from .models import Sizes, DefaultMeasurement, CustomMeasurement


@admin.register(Sizes)
class SizesAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'size_name', 'measurement_type', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__username', 'size_name']
    readonly_fields = ['timestamp', 'get_measurement_type_display']

    def measurement_type(self, obj):
        """Show if measurement is from custom or default"""
        # Check if any custom measurement field has data
        # Custom measurements use all detailed fields from 3 screens
        if obj.front_hight or obj.back_hight or obj.around_neck:
            return '✏️ Custom Measurement'
        return '📏 Default Measurement'
    measurement_type.short_description = 'Type'

    def get_measurement_type_display(self, obj):
        """Display measurement type in the form as readonly field"""
        if obj and obj.pk:  # Only show for existing objects
            if obj.front_hight or obj.back_hight or obj.around_neck:
                return '✏️ Custom Measurement'
            return '📏 Default Measurement'
        return '⚪ Not saved yet'
    get_measurement_type_display.short_description = 'Measurement Type'

    def get_fieldsets(self, _request, obj=None):
        """Return different fieldsets based on measurement type"""
        if obj is None:
            # Creating new object - show all fields
            return (
                ('Basic Information', {
                    'fields': ('user', 'size_name', 'get_measurement_type_display', 'timestamp')
                }),
                ('📐 Height Measurements (Screen 1)', {
                    'fields': (
                        'front_hight',
                        'back_hight',
                        'around_neck',
                        'around_legs',
                    ),
                    'description': 'From Custom Measurement Screen 1: Front Height, Back Height, Neck, Around Legs'
                }),
                ('📏 Movement Measurements (Screen 2)', {
                    'fields': (
                        'full_chest',
                        'half_chest',
                        'full_belly',
                        'half_belly',
                        'neck_to_center_belly',
                        'neck_to_chest',
                    ),
                    'description': 'From Custom Measurement Screen 2: Chest & Belly measurements'
                }),
                ('💪 Neck & Arm Measurements (Screen 3)', {
                    'fields': (
                        'shoulders_width',
                        'arm_tall',
                        'arm_width_one',
                        'arm_width_two',
                        'arm_width_three',
                        'arm_width_four',
                    ),
                    'description': 'From Custom Measurement Screen 3: Shoulder & Arm measurements'
                }),
            )

        # Editing existing object - check if custom or default
        is_custom = bool(obj.front_hight or obj.back_hight or obj.around_neck)

        if is_custom:
            # Custom Measurement - show all detailed fields grouped by screen
            return (
                ('Basic Information', {
                    'fields': ('user', 'size_name', 'get_measurement_type_display', 'timestamp')
                }),
                ('📐 Height Measurements (Screen 1)', {
                    'fields': (
                        'front_hight',
                        'back_hight',
                        'around_neck',
                        'around_legs',
                    ),
                    'description': '✏️ Custom measurements from Screen 1: Front Height, Back Height, Neck, Around Legs'
                }),
                ('📏 Movement Measurements (Screen 2)', {
                    'fields': (
                        'full_chest',
                        'half_chest',
                        'full_belly',
                        'half_belly',
                        'neck_to_center_belly',
                        'neck_to_chest',
                    ),
                    'description': '✏️ Custom measurements from Screen 2: Chest & Belly measurements'
                }),
                ('💪 Neck & Arm Measurements (Screen 3)', {
                    'fields': (
                        'shoulders_width',
                        'arm_tall',
                        'arm_width_one',
                        'arm_width_two',
                        'arm_width_three',
                        'arm_width_four',
                    ),
                    'description': '✏️ Custom measurements from Screen 3: Shoulder & Arm measurements'
                }),
            )
        else:
            # Default Measurement - show summary info only
            return (
                ('Basic Information', {
                    'fields': ('user', 'size_name', 'get_measurement_type_display', 'timestamp')
                }),
                ('📏 Default Measurement Info', {
                    'fields': (),
                    'description': '📋 This user selected a default/pre-defined size. No custom measurements were entered. The size_name field indicates which default measurement was selected.'
                }),
            )


@admin.register(DefaultMeasurement)
class DefaultMeasurementAdmin(admin.ModelAdmin):
    list_display = ['id', 'size_name_eng', 'size_name_ar', 'category', 'length', 'sleeves', 'chest', 'is_active', 'timestamp']
    list_filter = ['is_active', 'category', 'timestamp']
    search_fields = ['size_name', 'size_name_eng', 'size_name_ar']
    readonly_fields = ['timestamp', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('size_name', 'size_name_eng', 'size_name_ar', 'category', 'is_active')
        }),
        ('Frontend Display Measurements (shown to users)', {
            'fields': ('length', 'sleeves', 'chest'),
            'description': 'These measurements are displayed to users in the measurement selection screen'
        }),
        ('Front & Back Measurements', {
            'fields': (
                ('front_height', 'front_height_image'),
                ('back_height', 'back_height_image'),
            )
        }),
        ('Neck & Legs Measurements', {
            'fields': (
                ('neck_size', 'neck_size_image'),
                ('around_legs', 'around_legs_image'),
            )
        }),
        ('Chest & Belly Measurements', {
            'fields': (
                ('full_chest', 'full_chest_image'),
                ('half_chest', 'half_chest_image'),
                ('full_belly', 'full_belly_image'),
                ('half_belly', 'half_belly_image'),
            )
        }),
        ('Neck to Chest/Belly Measurements', {
            'fields': (
                ('neck_to_center_belly', 'neck_to_center_belly_image'),
                ('neck_to_chest_pocket', 'neck_to_chest_pocket_image'),
            )
        }),
        ('Shoulder & Arm Measurements', {
            'fields': (
                ('shoulder_width', 'shoulder_width_image'),
                ('arm_tall', 'arm_tall_image'),
                ('arm_width_1', 'arm_width_1_image'),
                ('arm_width_2', 'arm_width_2_image'),
                ('arm_width_3', 'arm_width_3_image'),
                ('arm_width_4', 'arm_width_4_image'),
            )
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'updated_at')
        }),
    )


# Custom Measurement hidden from admin
# @admin.register(CustomMeasurement)
# class CustomMeasurementAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'size_name', 'timestamp', 'updated_at']
#     list_filter = ['timestamp', 'user']
#     search_fields = ['user__username', 'size_name']
#     readonly_fields = ['timestamp', 'updated_at']
#
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('user', 'size_name')
#         }),
#         ('Front & Back Measurements', {
#             'fields': (
#                 ('front_height', 'front_height_image'),
#                 ('back_height', 'back_height_image'),
#             )
#         }),
#         ('Neck & Legs Measurements', {
#             'fields': (
#                 ('neck_size', 'neck_size_image'),
#                 ('around_legs', 'around_legs_image'),
#             )
#         }),
#         ('Chest & Belly Measurements', {
#             'fields': (
#                 ('full_chest', 'full_chest_image'),
#                 ('half_chest', 'half_chest_image'),
#                 ('full_belly', 'full_belly_image'),
#                 ('half_belly', 'half_belly_image'),
#             )
#         }),
#         ('Neck to Chest/Belly Measurements', {
#             'fields': (
#                 ('neck_to_center_belly', 'neck_to_center_belly_image'),
#                 ('neck_to_chest_pocket', 'neck_to_chest_pocket_image'),
#             )
#         }),
#         ('Shoulder & Arm Measurements', {
#             'fields': (
#                 ('shoulder_width', 'shoulder_width_image'),
#                 ('arm_tall', 'arm_tall_image'),
#                 ('arm_width_1', 'arm_width_1_image'),
#                 ('arm_width_2', 'arm_width_2_image'),
#                 ('arm_width_3', 'arm_width_3_image'),
#                 ('arm_width_4', 'arm_width_4_image'),
#             )
#         }),
#         ('Timestamps', {
#             'fields': ('timestamp', 'updated_at')
#         }),
#     )
