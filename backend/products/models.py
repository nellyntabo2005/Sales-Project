# products/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
import random
import string

class Category(models.Model):
    """
    Product categories for organization
    Supports parent-child hierarchy (e.g., Electronics > Phones > Smartphones)
    """
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, help_text="URL-friendly name")
    description = models.TextField(blank=True)
    
    # Self-referential parent-child relationship
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category (if any)"
    )
    
    # Visual
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    color = models.CharField(max_length=20, blank=True, help_text="Hex color code")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_full_path(self):
        """Get full category path (e.g., Electronics > Phones > Smartphones)"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
    
    @property
    def level(self):
        """Get category level in hierarchy (0 = root)"""
        if self.parent:
            return self.parent.level + 1
        return 0


class Supplier(models.Model):
    """
    Product suppliers/vendors
    """
    
    # Basic info
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, help_text="Supplier code (e.g., SUP-001)")
    contact_person = models.CharField(max_length=100, blank=True)
    
    # Contact
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Tax info
    tax_number = models.CharField(max_length=50, blank=True, help_text="KRA PIN")
    
    # Bank details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(default=False, help_text="Preferred supplier")
    
    # Payment terms
    payment_terms = models.IntegerField(default=30, help_text="Payment terms in days")
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['phone']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Generate supplier code: SUP-XXXX
            last_supplier = Supplier.objects.order_by('-id').first()
            if last_supplier and last_supplier.code:
                try:
                    last_num = int(last_supplier.code.split('-')[1])
                    self.code = f"SUP-{last_num + 1:04d}"
                except (IndexError, ValueError):
                    self.code = "SUP-0001"
            else:
                self.code = "SUP-0001"
        super().save(*args, **kwargs)


class Product(models.Model):
<<<<<<< HEAD
    """
    Main Product model for ERP/POS system
    """
    
    # === IDENTIFIERS ===
=======

    name = models.CharField(max_length=150)

    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    

>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
    sku = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Stock Keeping Unit - Auto-generated"
    )
    
    barcode = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="Product barcode (EAN-13 format)"
    )
<<<<<<< HEAD
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # === BASIC INFO ===
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    
    # === CATEGORY ===
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True
    )
    
    # === SUPPLIER ===
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True
    )
    
    supplier_sku = models.CharField(max_length=50, blank=True, help_text="Supplier's product code")
    
    # === PRICING (Multi-tier) ===
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Purchase cost from supplier"
    )
    
    retail_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Regular retail price"
    )
    
    wholesale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Wholesale price (10%+ discount)"
    )
    
    carton_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Carton/box price for bulk purchases"
    )
    
    carton_quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of units per carton"
    )
    
    # === STOCK MANAGEMENT ===
    stock_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current stock on hand"
    )
    
    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Alert when stock falls below this level"
    )
    
    reorder_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Quantity to order when reordering"
    )
    
    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Minimum stock level (never go below)"
    )
    
    maximum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum stock level (optional)"
    )
    
    # Unit of measurement
    UNIT_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('box', 'Box'),
        ('carton', 'Carton'),
        ('pack', 'Pack'),
    ]
    
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    
    # === TAX ===
    TAX_CHOICES = [
        (0, '0% (Zero Rated)'),
        (8, '8%'),
        (16, '16% (VAT Standard)'),
    ]
    
    tax_rate = models.IntegerField(choices=TAX_CHOICES, default=16)
    
    # === WEIGHT & DIMENSIONS (for shipping) ===
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Length in cm")
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # === STATUS ===
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_digital = models.BooleanField(default=False, help_text="Digital product (no shipping)")
    
    # === IMAGES ===
    main_image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    # === NOTES ===
    notes = models.TextField(blank=True)
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_purchased_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['supplier']),
            models.Index(fields=['is_active']),
            models.Index(fields=['stock_quantity']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        """Auto-generate SKU and barcode if not set"""
        if not self.sku:
            # Generate SKU: CAT-XXXX
            category_code = self.category.name[:3].upper() if self.category else 'GEN'
            last_product = Product.objects.order_by('-id').first()
            if last_product and last_product.sku:
                try:
                    last_num = int(last_product.sku.split('-')[-1])
                    self.sku = f"{category_code}-{last_num + 1:06d}"
                except (IndexError, ValueError):
                    self.sku = f"{category_code}-000001"
            else:
                self.sku = f"{category_code}-000001"
        
        # Auto-generate barcode if not set (simple format)
        if not self.barcode:
            # Use SKU as barcode or generate random
            self.barcode = self.sku
        
        # Validate wholesale price is less than retail price
        if self.wholesale_price and self.wholesale_price >= self.retail_price:
            raise ValidationError("Wholesale price must be less than retail price")
        
        # Validate carton price
        if self.carton_price and self.carton_quantity > 1:
            unit_carton_price = self.carton_price / self.carton_quantity
            if unit_carton_price >= self.retail_price:
                raise ValidationError("Carton price per unit must be less than retail price")
        
        super().save(*args, **kwargs)
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price > 0:
            return ((self.retail_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        """Check if product needs reordering"""
        return self.stock_quantity <= self.reorder_level
    
    @property
    def stock_value(self):
        """Calculate total stock value"""
        return self.stock_quantity * self.cost_price
    
    def get_price_for_customer(self, customer):
        """Get appropriate price based on customer tier"""
        if customer and customer.pricing_tier == 'wholesale' and self.wholesale_price:
            return self.wholesale_price
        return self.retail_price
    
    def update_stock(self, quantity, transaction_type='sale'):
        """
        Update stock quantity with validation
        transaction_type: 'sale', 'purchase', 'return', 'adjustment'
        """
        from inventory.models import StockMovement  # We'll create this later
        
        if transaction_type == 'sale':
            if self.stock_quantity < quantity:
                raise ValidationError(f"Insufficient stock. Available: {self.stock_quantity}")
            self.stock_quantity -= quantity
        elif transaction_type == 'purchase':
            self.stock_quantity += quantity
        elif transaction_type == 'return':
            self.stock_quantity += quantity
        elif transaction_type == 'adjustment':
            self.stock_quantity = quantity
        
        self.save(update_fields=['stock_quantity', 'updated_at'])
        
        # Record stock movement
        # StockMovement.objects.create(...)
        
        return True


class ProductImage(models.Model):
    """
    Additional product images
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.product.name}"


    
=======

    

    stock_quantity = models.IntegerField(default=0)

    reserved_stock = models.IntegerField(default=0)

    def available_stock(self):
        return self.stock_quantity - self.reserved_stock

    def __str__(self):
        return self.name
    

class Supplier(models.Model):

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    
    def __str__(self):
        return self.name
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
