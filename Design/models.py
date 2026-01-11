from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

# Create your models here.

# ================HOME PAGE CATEGORY SELECTION====================
class HomePageSelectionCategory(models.Model):
    main_category_name_eng = models.CharField(max_length=80, default="")
    main_category_name_arb = models.CharField(max_length=80, default="")
    duration_delivery_period = models.CharField(max_length=80, default="")
    initial_price = models.DecimalField(max_digits=9, decimal_places=3)
    cover = CloudinaryField('image', blank=True, null=True, folder="MainCat")
    review_rate = models.IntegerField(default= 0 )
    isHidden = models.BooleanField(default=False)
    is_comming_soon = models.BooleanField(default=False)
    priority = models.IntegerField(default=0, help_text="Lower value = higher priority (appears first)")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.main_category_name_eng

# ================Category such us Fabric, buttons , Ghola================

#================ FABRIC TYPE (Base Fabric) ================
class FabricType(models.Model):
    """Base fabric model without color - e.g., 'Cotton Satin', 'Silk'"""

    # Choices for season
    SEASON_CHOICES = (
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('all_season', 'All Season'),
        ('spring', 'Spring'),
        ('autumn', 'Autumn'),
    )

    # Choices for category type
    CATEGORY_TYPE_CHOICES = (
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('economy', 'Economy'),
        ('luxury', 'Luxury'),
    )

    fabric_name_eng = models.CharField(max_length=300)
    fabric_name_arb = models.CharField(max_length=300)
    base_price = models.DecimalField(max_digits=9, decimal_places=3)
    cover = CloudinaryField('image', blank=True, null=True, folder="FabricType")
    isHidden = models.BooleanField(default=False)
    priority = models.IntegerField(default=0, help_text="Lower value = higher priority (appears first)")
    timestamp = models.DateTimeField(auto_now_add=True)

    # New fields based on UI design
    originality = models.CharField(max_length=100, blank=True, null=True, help_text="Origin country e.g., Kuwait, Italy")
    originality_arb = models.CharField(max_length=100, blank=True, null=True, help_text="Origin country in Arabic")
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='all_season')
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default='standard', help_text="Fabric category: Premium, Standard, etc.")
    features = models.JSONField(default=list, blank=True, help_text="List of features e.g., ['Anti-Static', 'Anti-Breakable', 'Easy Iron']")
    features_arb = models.JSONField(default=list, blank=True, help_text="List of features in Arabic")
    weight = models.CharField(max_length=50, blank=True, null=True, help_text="Weight description e.g., 'per sq / m'")
    weight_arb = models.CharField(max_length=50, blank=True, null=True, help_text="Weight description in Arabic")
    composition = models.CharField(max_length=200, blank=True, null=True, help_text="Fabric composition e.g., '100% Polyester'")
    composition_arb = models.CharField(max_length=200, blank=True, null=True, help_text="Fabric composition in Arabic")
    softness_grade = models.IntegerField(default=3, help_text="Softness to Solidness grade from 1 (Soft) to 5 (Solid)")

    def __str__(self):
        return self.fabric_name_eng

    class Meta:
        ordering = ['priority', '-timestamp']
        verbose_name = "Fabric Type"
        verbose_name_plural = "Fabric Types"

#================ FABRIC COLOR (Color Variants) ================
class FabricColor(models.Model):
    """Color variants of a fabric - e.g., 'White Cotton Satin', 'Beige Cotton Satin'"""
    fabric_type = models.ForeignKey(FabricType, on_delete=models.CASCADE, related_name="colors")
    color_name_eng = models.CharField(max_length=100)
    color_name_arb = models.CharField(max_length=100)
    hex_color = models.CharField(max_length=7, default='#FFFFFF', help_text="Hex color code (e.g., #FFFFFF)")
    cover = CloudinaryField('image', blank=True, null=True, folder="FabricColors")
    quantity = models.IntegerField(default=0)
    inStock = models.BooleanField(default=True)
    price_adjustment = models.DecimalField(
        max_digits=9,
        decimal_places=3,
        default=0.000,
        help_text="Additional price for this color (can be positive or negative)"
    )
    priority = models.IntegerField(default=0, help_text="Lower value = higher priority (appears first)")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fabric_type.fabric_name_eng} - {self.color_name_eng}"

    @property
    def total_price(self):
        """Calculate total price: base fabric price + color adjustment"""
        return self.fabric_type.base_price + self.price_adjustment

    class Meta:
        ordering = ['priority', '-timestamp']
        verbose_name = "Fabric Color"
        verbose_name_plural = "Fabric Colors"
        unique_together = ['fabric_type', 'color_name_eng']

#================ class ProductDescription================

#================ GHOLA TYPE ================

class GholaType(models.Model):
    ghola_type_name_eng = models.CharField(max_length=300)
    ghola_type_name_arb = models.CharField(max_length=300)

    # FK to FabricType (Cotton, Silk, etc.) - for filtering
    fabric_type = models.ForeignKey(FabricType, on_delete=models.CASCADE, null=True, blank=True, related_name="ghola_types")

    # FK to FabricColor (specific color from that fabric's colors)
    fabric_color = models.ForeignKey(FabricColor, on_delete=models.CASCADE, null=True, blank=True, related_name="ghola_types")

    priority = models.IntegerField(default=0, help_text="Lower value = higher priority (appears first)")
    timestamp = models.DateTimeField(auto_now_add=True)
    initial_price = models.DecimalField(max_digits=9, decimal_places=3)
    cover = CloudinaryField('image', blank=True, null=True, folder="GholaType", help_text="Image shown on dishdasha preview")
    cover_option = CloudinaryField('image', blank=True, null=True, folder="GholaType/Options", help_text="Image shown in selection cards/options")
    is_button_hidden = models.BooleanField(default=False, help_text="If True, button will be rendered below collar (hidden)")

    def __str__(self):
        color_name = self.fabric_color.color_name_eng if self.fabric_color else "No Color"
        return f"{self.ghola_type_name_eng} - {color_name}"

    class Meta:
        ordering = ['priority', '-timestamp']
        verbose_name = "Collar Type (Ghola)"
        verbose_name_plural = "Collar Types (Ghola)"
    

#================ Sleeve TYPE ================

class SleevesType(models.Model):
    sleeves_type_name_eng = models.CharField(max_length=300)
    sleeves_type_name_arb = models.CharField(max_length=300)

    # FK to FabricType (Cotton, Silk, etc.) - for filtering
    fabric_type = models.ForeignKey(FabricType, on_delete=models.CASCADE, null=True, blank=True, related_name="sleeve_types")

    # FK to FabricColor (specific color from that fabric's colors)
    fabric_color = models.ForeignKey(FabricColor, on_delete=models.CASCADE, null=True, blank=True, related_name="sleeve_types")

    is_right_side = models.BooleanField(default=False)
    priority = models.IntegerField(default=0, help_text="Lower value = higher priority (appears first)")
    timestamp = models.DateTimeField(auto_now_add=True)
    initial_price = models.DecimalField(max_digits=9, decimal_places=3)
    cover = CloudinaryField('image', blank=True, null=True, folder="SleevesType", help_text="Image shown on dishdasha preview")
    cover_option = CloudinaryField('image', blank=True, null=True, folder="SleevesType/Options", help_text="Image shown in selection cards/options")

    def __str__(self):
        color_name = self.fabric_color.color_name_eng if self.fabric_color else "No Color"
        return f"{self.sleeves_type_name_eng} - {color_name}"

    class Meta:
        ordering = ['priority', '-timestamp']
        verbose_name = "Sleeve Type"
        verbose_name_plural = "Sleeve Types"

#================ Pocket TYPE ================

class PocketType(models.Model):
    pocket_type_name_eng = models.CharField(max_length=300)
    pocket_type_name_arb = models.CharField(max_length=300)

    # FK to FabricType (Cotton, Silk, etc.) - for filtering
    fabric_type = models.ForeignKey(FabricType, on_delete=models.CASCADE, null=True, blank=True, related_name="pocket_types")

    # FK to FabricColor (specific color from that fabric's colors)
    fabric_color = models.ForeignKey(FabricColor, on_delete=models.CASCADE, null=True, blank=True, related_name="pocket_types")

    priority = models.IntegerField(default=0, help_text="Lower value = higher priority (appears first)")
    timestamp = models.DateTimeField(auto_now_add=True)
    initial_price = models.DecimalField(max_digits=9, decimal_places=3)
    cover = CloudinaryField('image', blank=True, null=True, folder="PocketType", help_text="Image shown on dishdasha preview")
    cover_option = CloudinaryField('image', blank=True, null=True, folder="PocketType/Options", help_text="Image shown in selection cards/options")

    def __str__(self):
        color_name = self.fabric_color.color_name_eng if self.fabric_color else "No Color"
        return f"{self.pocket_type_name_eng} - {color_name}"

    class Meta:
        ordering = ['priority', '-timestamp']
        verbose_name = "Pocket Type"
        verbose_name_plural = "Pocket Types"

#================ Button TYPE ================

class ButtonType(models.Model):
    button_type_name_eng = models.CharField(max_length=300)
    button_type_name_arb = models.CharField(max_length=300)

    # FK to FabricType (Cotton, Silk, etc.) - for filtering
    fabric_type = models.ForeignKey(FabricType, on_delete=models.CASCADE, null=True, blank=True, related_name="button_types")

    # FK to FabricColor (specific color from that fabric's colors)
    fabric_color = models.ForeignKey(FabricColor, on_delete=models.CASCADE, null=True, blank=True, related_name="button_types")

    priority = models.IntegerField(default=0, help_text="Lower value = higher priority (appears first)")
    timestamp = models.DateTimeField(auto_now_add=True)
    inStock = models.BooleanField(default=True)
    initial_price = models.DecimalField(max_digits=9, decimal_places=3)
    cover = CloudinaryField('image', blank=True, null=True, folder="ButtonType", help_text="Image shown on dishdasha preview")
    cover_option = CloudinaryField('image', blank=True, null=True, folder="ButtonType/Options", help_text="Image shown in selection cards/options")

    def __str__(self):
        color_name = self.fabric_color.color_name_eng if self.fabric_color else "No Color"
        return f"{self.button_type_name_eng} - {color_name}"

    class Meta:
        ordering = ['priority', '-timestamp']
        verbose_name = "Button Type"
        verbose_name_plural = "Button Types"



#================ Body TYPE ================

class BodyType(models.Model):
    body_type_name_eng = models.CharField(max_length=300)
    body_type_name_arb = models.CharField(max_length=300)

    # FK to FabricType (Cotton, Silk, etc.) - for filtering
    fabric_type = models.ForeignKey(FabricType, on_delete=models.CASCADE, null=True, blank=True, related_name="body_types")

    # FK to FabricColor (specific color from that fabric's colors)
    fabric_color = models.ForeignKey(FabricColor, on_delete=models.CASCADE, null=True, blank=True, related_name="body_types")


    timestamp = models.DateTimeField(auto_now_add=True)
    initial_price = models.DecimalField(max_digits=9, decimal_places=3)
    cover = CloudinaryField('image', blank=True, null=True, folder="BodyType", help_text="Image shown on dishdasha preview")
    cover_option = CloudinaryField('image', blank=True, null=True, folder="BodyType/Options", help_text="Image shown in selection cards/options")

    def __str__(self):
        color_name = self.fabric_color.color_name_eng if self.fabric_color else "No Color"
        return f"{self.body_type_name_eng} - {color_name}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Body Type"
        verbose_name_plural = "Body Types"

#======================= END-USER DESIGN========================
class UserDesign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='designs')
    design_name = models.CharField(max_length=200, blank=True, null=True, help_text="Custom name for this design")
    timestamp = models.DateTimeField(auto_now_add=True)
    initial_size_selected = models.ForeignKey(HomePageSelectionCategory, on_delete=models.CASCADE, null=True, blank=True, related_name="user_designs_category")

    # FK to FabricColor - all design components are nullable to allow incomplete designs
    main_body_fabric_color = models.ForeignKey(FabricColor, on_delete=models.CASCADE, null=True, blank=True, related_name="user_designs")

    selected_coller_type = models.ForeignKey(GholaType, on_delete=models.CASCADE, null=True, blank=True, related_name="selected_collar_designs")
    selected_sleeve_left_type = models.ForeignKey(SleevesType, on_delete=models.CASCADE, null=True, blank=True, related_name="selected_sleeve_left_type")
    selected_sleeve_right_type = models.ForeignKey(SleevesType, on_delete=models.CASCADE, null=True, blank=True)

    # FIX ISSUE 1: Add pocket and button selections
    selected_pocket_type = models.ForeignKey(PocketType, on_delete=models.CASCADE, null=True, blank=True, related_name="selected_pocket_designs")
    selected_button_type = models.ForeignKey(ButtonType, on_delete=models.CASCADE, null=True, blank=True, related_name="selected_button_designs")

    selected_body_type = models.ForeignKey(BodyType, on_delete=models.CASCADE, null=True, blank=True, related_name="selected_body_designs")

    design_Total = models.DecimalField(max_digits=9, decimal_places=3, default=0.000)

    def __str__(self):
        if self.design_name:
            return self.design_name
        return f"{self.user.username}'s Design #{self.id}"

    class Meta:
        verbose_name = "User Design"
        verbose_name_plural = "User Designs"


#======================= INVENTORY TRANSACTION MODEL ========================
class InventoryTransaction(models.Model):
    """Track all inventory changes for fabric colors"""

    TRANSACTION_TYPE_CHOICES = (
        ('ORDER', 'Order Placed'),
        ('CANCEL', 'Order Cancelled'),
        ('RESTOCK', 'Manual Restock'),
        ('ADJUSTMENT', 'Manual Adjustment'),
    )

    fabric_color = models.ForeignKey(
        FabricColor,
        on_delete=models.CASCADE,
        related_name='inventory_transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity_change = models.IntegerField(help_text="Negative for deduction, positive for addition")
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    reference_order = models.CharField(max_length=100, blank=True, null=True, help_text="Order invoice number if applicable")
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fabric_color.color_name_eng} - {self.transaction_type} ({self.quantity_change}) - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Inventory Transaction"
        verbose_name_plural = "Inventory Transactions"


#======================= DESIGN SCREENSHOT MODEL ========================
class DesignScreenshot(models.Model):
    """
    Store screenshots for design configurations to avoid regenerating identical designs.
    Uses a hash of component IDs to identify unique designs.
    """

    design_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="MD5 hash of all component IDs to uniquely identify design configuration"
    )
    screenshot_url = models.URLField(
        max_length=500,
        help_text="Cloudinary URL of the design screenshot"
    )
    cloudinary_public_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Cloudinary public ID for managing the image"
    )

    # Store individual component IDs for reference and debugging
    fabric_color_id = models.IntegerField(null=True, blank=True)
    collar_id = models.IntegerField(null=True, blank=True)
    sleeve_left_id = models.IntegerField(null=True, blank=True)
    sleeve_right_id = models.IntegerField(null=True, blank=True)
    pocket_id = models.IntegerField(null=True, blank=True)
    button_id = models.IntegerField(null=True, blank=True)
    body_id = models.IntegerField(null=True, blank=True)

    # Metadata
    times_reused = models.IntegerField(
        default=0,
        help_text="Number of times this screenshot was reused instead of regenerating"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Design Screenshot {self.design_hash[:8]}... (reused {self.times_reused} times)"

    class Meta:
        verbose_name = "Design Screenshot"
        verbose_name_plural = "Design Screenshots"
        ordering = ['-created_at']
