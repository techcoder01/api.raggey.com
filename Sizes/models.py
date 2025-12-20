from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

# Create your models here.

# Default Measurements (Admin-created, visible to all users)
class DefaultMeasurement(models.Model):
    CATEGORY_CHOICES = [
        ('child', 'Child'),
        ('adult', 'Adult'),
        ('baby', 'Baby'),
    ]

    size_name = models.CharField(max_length=80, unique=True)
    size_name_eng = models.CharField(max_length=80, default='', help_text="English name (e.g., 'Newborn', '3 Months')")
    size_name_ar = models.CharField(max_length=80, default='', help_text="Arabic name (e.g., 'مولود جديد', '3 أشهر')")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='child', help_text="Category: child, adult, or baby")

    # Frontend display fields (shown to users in measurement selection screen)
    length = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Length/Height in inches (طول)")
    sleeves = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Sleeves measurement in inches (الاكمام)")
    chest = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Chest measurement in inches (الصدر)")

    # Detailed measurement fields for tailor (with their instruction images)
    front_height = models.CharField(max_length=80)
    front_height_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    back_height = models.CharField(max_length=80)
    back_height_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    neck_size = models.CharField(max_length=80)
    neck_size_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    around_legs = models.CharField(max_length=80)
    around_legs_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    full_chest = models.CharField(max_length=80)
    full_chest_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    half_chest = models.CharField(max_length=80)
    half_chest_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    full_belly = models.CharField(max_length=80)
    full_belly_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    half_belly = models.CharField(max_length=80)
    half_belly_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    neck_to_center_belly = models.CharField(max_length=80)
    neck_to_center_belly_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    neck_to_chest_pocket = models.CharField(max_length=80)
    neck_to_chest_pocket_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    shoulder_width = models.CharField(max_length=80)
    shoulder_width_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    arm_tall = models.CharField(max_length=80)
    arm_tall_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    arm_width_1 = models.CharField(max_length=80)
    arm_width_1_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    arm_width_2 = models.CharField(max_length=80)
    arm_width_2_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    arm_width_3 = models.CharField(max_length=80)
    arm_width_3_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    arm_width_4 = models.CharField(max_length=80)
    arm_width_4_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Instructions")

    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['timestamp']  # Oldest first (Newborn -> Two Years)
        verbose_name = 'Default Measurement'
        verbose_name_plural = 'Default Measurements'

    def __str__(self):
        return self.size_name


# Custom Measurements (User-created, private to each user)
class CustomMeasurement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_measurements')
    size_name = models.CharField(max_length=80)

    # Measurement fields with their instruction images
    front_height = models.CharField(max_length=80)
    front_height_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    back_height = models.CharField(max_length=80)
    back_height_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    neck_size = models.CharField(max_length=80)
    neck_size_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    around_legs = models.CharField(max_length=80)
    around_legs_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    full_chest = models.CharField(max_length=80)
    full_chest_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    half_chest = models.CharField(max_length=80)
    half_chest_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    full_belly = models.CharField(max_length=80)
    full_belly_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    half_belly = models.CharField(max_length=80)
    half_belly_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    neck_to_center_belly = models.CharField(max_length=80)
    neck_to_center_belly_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    neck_to_chest_pocket = models.CharField(max_length=80)
    neck_to_chest_pocket_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    shoulder_width = models.CharField(max_length=80)
    shoulder_width_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    arm_tall = models.CharField(max_length=80)
    arm_tall_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    arm_width_1 = models.CharField(max_length=80)
    arm_width_1_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    arm_width_2 = models.CharField(max_length=80)
    arm_width_2_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    arm_width_3 = models.CharField(max_length=80)
    arm_width_3_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    arm_width_4 = models.CharField(max_length=80)
    arm_width_4_image = CloudinaryField('image', blank=True, null=True, folder="Measurements/Custom")

    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Custom Measurement'
        verbose_name_plural = 'Custom Measurements'
        unique_together = ['user', 'size_name']  # Each user can have unique measurement names

    def __str__(self):
        return f"{self.user.username} - {self.size_name}"


# Keep the old Sizes model for backward compatibility (can be removed later if not needed)
class Sizes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    size_name = models.CharField(max_length=80)
    front_hight = models.CharField(max_length=80)
    back_hight = models.CharField(max_length=80)
    around_neck = models.CharField(max_length=80)
    around_legs = models.CharField(max_length=80)
    full_chest = models.CharField(max_length=80)
    half_chest = models.CharField(max_length=80)
    full_belly = models.CharField(max_length=80)
    half_belly = models.CharField(max_length=80)
    neck_to_center_belly = models.CharField(max_length=80)
    neck_to_chest = models.CharField(max_length=80)
    shoulders_width = models.CharField(max_length=80)
    arm_tall = models.CharField(max_length=80)
    arm_width_one = models.CharField(max_length=80)
    arm_width_two = models.CharField(max_length=80)
    arm_width_three = models.CharField(max_length=80)
    arm_width_four = models.CharField(max_length=80)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username