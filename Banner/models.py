from django.db import models
from cloudinary.models import CloudinaryField

class Banner(models.Model):
    """
    Home screen banner images for English and Arabic languages
    """
    title = models.CharField(max_length=200, help_text="Banner title (for admin reference)")

    # Banner images
    image_en = CloudinaryField(
        'banner_english',
        help_text="Banner image for English language"
    )
    image_ar = CloudinaryField(
        'banner_arabic',
        help_text="Banner image for Arabic language"
    )

    # Status and ordering
    is_active = models.BooleanField(
        default=True,
        help_text="Active banners are shown in the app"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Banner"
        verbose_name_plural = "Banners"

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"
