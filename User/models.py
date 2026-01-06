from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from Fee.models import Fee


User._meta.get_field('email')._unique = True
User._meta.get_field('email').blank = False
User._meta.get_field('email').null = False

PERMISSION_CHOICES = (
    ("User", "User"),
    ("Admin", "Admin"),
    ("Data-Entry", "Data-Entry"),
    ("Partner", "Partner"),
    ("Accountant", "Accountant"),
    ("Driver", "Driver"),
    ("Vendor", "Vendor"),

)
# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, default="")
    premission = models.CharField(max_length=80, choices=PERMISSION_CHOICES)
    phone_number = models.CharField(max_length=20, null=True, blank=True, help_text="User phone number with country code")

    # FCM & Device Information (for push notifications)
    fcm_token = models.TextField(null=True, blank=True, help_text="Firebase Cloud Messaging token for push notifications")
    device_name = models.CharField(max_length=200, null=True, blank=True, help_text="Device name (e.g., Samsung Galaxy S21)")
    device_id = models.CharField(max_length=200, null=True, blank=True, help_text="Unique device identifier")
    device_type = models.CharField(max_length=50, null=True, blank=True, help_text="Device type (android/ios)")
    last_fcm_update = models.DateTimeField(auto_now=True, help_text="Last time FCM token was updated")

    def __str__(self):
        return self.user.username
    
class Address(models.Model):
    ADDRESS_TYPE_CHOICES = (
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')

    # Location coordinates
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Full formatted address string
    full_address = models.TextField(null=True, blank=True)

    # Address details
    governorate = models.CharField(max_length=100, default='', blank=True, help_text="Governorate (e.g., Ahmadi)")
    area = models.CharField(max_length=100, default='', blank=True, help_text="Area/Region (e.g., Sabahiya)")
    block = models.CharField(max_length=50, default='', blank=True, help_text="Block number")
    street = models.CharField(max_length=50, default='', blank=True, help_text="Street number")
    building = models.CharField(max_length=50, default='', blank=True, help_text="Building/House number")
    apartment = models.CharField(max_length=50, null=True, blank=True, help_text="Apartment number")
    floor = models.CharField(max_length=50, null=True, blank=True, help_text="Floor number")

    # Contact information
    full_name = models.CharField(max_length=200, default='', blank=True, help_text="Recipient's full name")
    phone_number = models.CharField(max_length=20, help_text="Contact phone number with country code")

    # Address labeling
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='home', help_text="Address type (Home/Work/Other)")
    custom_label = models.CharField(max_length=100, null=True, blank=True, help_text="Custom address label if type is 'other'")

    # Settings
    isDefault = models.BooleanField(default=False, help_text="Is this the default address?")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-isDefault', '-created_at']

    def __str__(self):
        # Show more details for admin dropdown: Type - Area (Block X, Street Y)
        location = f"{self.area}" if self.area else "No area"
        if self.block:
            location += f" (Block {self.block}"
            if self.street:
                location += f", Street {self.street}"
            location += ")"
        return f"{self.get_address_type_display()} - {location}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        permission = "Admin" if instance.is_superuser else "User"
        Profile.objects.create(user=instance, premission=permission)


class ForceLogoutUser(models.Model):
    """
    Users in this table will be force logged out on next API request
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='force_logout')
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'force_logout_users'
        verbose_name = 'Force Logout User'
        verbose_name_plural = 'Force Logout Users'

    def __str__(self):
        return f"Force Logout: {self.user.username}"

    @classmethod
    def should_logout(cls, user):
        """Check if user should be force logged out"""
        return cls.objects.filter(user=user).exists()

    @classmethod
    def add_user(cls, user, reason=None):
        """Add user to force logout list"""
        obj, created = cls.objects.get_or_create(user=user, defaults={'reason': reason})
        return obj

    @classmethod
    def remove_user(cls, user):
        """Remove user from force logout list (after they login again)"""
        cls.objects.filter(user=user).delete()