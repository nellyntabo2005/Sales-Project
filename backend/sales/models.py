# sales/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
from datetime import datetime

# Import from other apps
from customers.models import Customer
from users.models import User

# We'll reference Product with string to avoid circular import
# We'll add the Product import when creating the relationship

class Sale(models.Model):
    """
    Sale/Transaction model - Core of POS system.
    Records each sale transaction.
    """
    
    # === IDENTIFIERS ===
    sale_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Human-readable sale number (e.g., INV-20241215-0001)"
    )
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    # === STATUS ===
    SALE_STATUS = [
        ('completed', 'Completed'),
        ('pending', 'Pending Payment'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('voided', 'Voided'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=SALE_STATUS,
        default='pending',
        db_index=True
    )
    
    PAYMENT_STATUS = [
        ('paid', 'Fully Paid'),
        ('partial', 'Partially Paid'),
        ('unpaid', 'Unpaid'),
        ('overpaid', 'Overpaid'),
    ]
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='unpaid',
        db_index=True
    )
    
    # === RELATIONSHIPS ===
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales',
        help_text="Customer who made the purchase"
    )
    
    cashier = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='sales_processed',
        help_text="Cashier who processed the sale"
    )
    
    # For manager override (e.g., voiding transactions)
    voided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_voided',
        help_text="Manager who voided this sale"
    )
    
    # === FINANCIAL TOTALS ===
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total before tax and discount"
    )
    
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total discount applied"
    )
    
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage applied"
    )
    
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total tax amount (e.g., VAT 16%)"
    )
    
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('16.00'),  # Kenya VAT is 16%
        help_text="Tax rate applied to items"
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Final total = subtotal - discount + tax"
    )
    
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount paid by customer"
    )
    
    change_due = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Change to return to customer"
    )
    
    # === LOYALTY & REWARDS ===
    loyalty_points_earned = models.IntegerField(default=0)
    loyalty_points_redeemed = models.IntegerField(default=0)
    loyalty_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Discount from loyalty points"
    )
    
    # === NOTES ===
    notes = models.TextField(blank=True, help_text="Sale notes (e.g., special instructions)")
    void_reason = models.TextField(blank=True, help_text="Reason if sale is voided/cancelled")
    
    # === TIMESTAMPS ===
    sale_date = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-sale_date']
        indexes = [
            models.Index(fields=['sale_id']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['sale_date']),
            models.Index(fields=['customer', 'sale_date']),
            models.Index(fields=['cashier', 'sale_date']),
        ]
        verbose_name = 'Sale'
        verbose_name_plural = 'Sales'
    
    def __str__(self):
        return f"{self.sale_id} - {self.customer.name if self.customer else 'Walk-in Customer'} - {self.total}"
    
    def save(self, *args, **kwargs):
        """Auto-generate sale_id if not set"""
        if not self.sale_id:
            # Format: INV-YYYYMMDD-XXXX
            today = datetime.now()
            date_str = today.strftime('%Y%m%d')
            
            # Get last sale number for today
            last_sale = Sale.objects.filter(
                sale_id__startswith=f'INV-{date_str}'
            ).order_by('-sale_id').first()
            
            if last_sale:
                last_num = int(last_sale.sale_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.sale_id = f"INV-{date_str}-{new_num:04d}"
        
        # Calculate change due
        if self.amount_paid >= self.total:
            self.change_due = self.amount_paid - self.total
            if self.amount_paid > self.total:
                self.payment_status = 'overpaid'
            else:
                self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.change_due = Decimal('0.00')
            self.payment_status = 'partial'
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """
        Recalculate all totals from sale items
        Called when items are added/removed/updated
        """
        items = self.items.all()
        
        # Calculate subtotal from items
        subtotal = sum(item.subtotal for item in items)
        
        # Apply discount
        discount = subtotal * (self.discount_percentage / 100)
        
        # Calculate tax on discounted amount
        taxable_amount = subtotal - discount
        tax = taxable_amount * (self.tax_rate / 100)
        
        # Final total
        total = taxable_amount + tax - self.loyalty_discount
        
        self.subtotal = subtotal
        self.discount_amount = discount
        self.tax_amount = tax
        self.total = total
        self.save(update_fields=['subtotal', 'discount_amount', 'tax_amount', 'total'])
        
        return self.total
    
    def add_loyalty_points(self):
        """
        Add loyalty points to customer based on sale
        Rule: 1 point per 100 KES spent
        """
        if self.customer and self.status == 'completed':
            points_earned = int(self.total / 100)
            if points_earned > 0:
                self.loyalty_points_earned = points_earned
                self.customer.add_loyalty_points(points_earned)
                self.save(update_fields=['loyalty_points_earned'])
    
    def void_sale(self, voided_by_user, reason):
        """
        Void a sale (reverse stock, refund points)
        """
        if self.status == 'completed':
            # Reverse stock for each item
            for item in self.items.all():
                item.product.stock_quantity += item.quantity
                item.product.save(update_fields=['stock_quantity'])
            
            # Reverse loyalty points
            if self.customer and self.loyalty_points_earned > 0:
                self.customer.loyalty_points -= self.loyalty_points_earned
                self.customer.save(update_fields=['loyalty_points'])
            
            # Update sale status
            self.status = 'voided'
            self.voided_by = voided_by_user
            self.void_reason = reason
            self.voided_at = datetime.now()
            self.save()
            
            return True
        return False


class SaleItem(models.Model):
    """
    Individual items within a sale (cart items)
    """
    is_returned = models.BooleanField(default=False, help_text="Has this item been returned?")
    returned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    product = models.ForeignKey(
        'products.Product',  # String reference to avoid circular import
        on_delete=models.PROTECT,
        related_name='sale_items'
    )
    
    # === PRODUCT SNAPSHOT (in case product changes later) ===
    product_name = models.CharField(max_length=200, help_text="Product name at time of sale")
    product_sku = models.CharField(max_length=100, help_text="Product SKU at time of sale")
    product_barcode = models.CharField(max_length=100, blank=True)
    
    # === PRICING ===
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price per unit at time of sale"
    )
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0.01)]
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="unit_price × quantity"
    )
    
    # Individual item discount
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="subtotal - discount"
    )
    
    # === TIMESTAMP ===
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['sale']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.quantity} × {self.product_name} (${self.total})"
    
    def save(self, *args, **kwargs):
        """Calculate totals before saving"""
        self.subtotal = self.unit_price * self.quantity
        self.discount_amount = self.subtotal * (self.discount_percentage / 100)
        self.total = self.subtotal - self.discount_amount
        
        # Update sale totals
        super().save(*args, **kwargs)
        
        # Update the parent sale's totals
        self.sale.calculate_totals()
    
    def delete(self, *args, **kwargs):
        """Update sale totals when item is deleted"""
        sale = self.sale
        super().delete(*args, **kwargs)
        sale.calculate_totals()


class Payment(models.Model):
    """
    Payment record for a sale
    Supports multiple payment methods per sale
    """
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('loyalty', 'Loyalty Points'),
        ('mixed', 'Mixed Payment'),
    ]
    
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # For M-Pesa specific fields
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    mpesa_phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # For card payments
    card_last_four = models.CharField(max_length=4, blank=True)
    card_transaction_id = models.CharField(max_length=100, blank=True)
    
    # For loyalty points redemption
    points_used = models.IntegerField(default=0, help_text="Loyalty points used for this payment")
    
    # General
    reference_number = models.CharField(max_length=100, blank=True, help_text="External reference")
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Recorded by
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payments_recorded')
    
    class Meta:
        ordering = ['payment_date']
    
    def __str__(self):
        return f"{self.payment_method} - {self.amount} for {self.sale.sale_id}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update sale's amount paid
        total_paid = self.sale.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        self.sale.amount_paid = total_paid
        self.sale.save(update_fields=['amount_paid', 'payment_status'])


class Receipt(models.Model):
    """
    Receipt generated for a sale
    """
    
    sale = models.OneToOneField(
        Sale,
        on_delete=models.CASCADE,
        related_name='receipt'
    )
    
    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Receipt content
    receipt_html = models.TextField(blank=True, help_text="HTML version for email")
    receipt_text = models.TextField(blank=True, help_text="Text version for printing")
    
    # Delivery methods
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    sent_via_whatsapp = models.BooleanField(default=False)
    printed = models.BooleanField(default=False)
    
    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.sale.sale_id}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Format: RCP-YYYYMMDD-XXXX
            from datetime import datetime
            today = datetime.now()
            date_str = today.strftime('%Y%m%d')
            
            last_receipt = Receipt.objects.filter(
                receipt_number__startswith=f'RCP-{date_str}'
            ).order_by('-receipt_number').first()
            
            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.receipt_number = f"RCP-{date_str}-{new_num:04d}"
        
        # Generate receipt content if not set
        if not self.receipt_text:
            self.receipt_text = self.generate_text_receipt()
        
        super().save(*args, **kwargs)
    
    def generate_text_receipt(self):
        """Generate plain text receipt for printing"""
        sale = self.sale
        lines = []
        
        lines.append("=" * 48)
        lines.append("YOUR STORE NAME".center(48))
        lines.append("Your Address Line 1".center(48))
        lines.append("Your Address Line 2".center(48))
        lines.append("Tel: 0712345678".center(48))
        lines.append("=" * 48)
        lines.append(f"Invoice: {sale.sale_id}")
        lines.append(f"Date: {sale.sale_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Cashier: {sale.cashier.get_full_name() or sale.cashier.username}")
        lines.append(f"Customer: {sale.customer.name if sale.customer else 'Walk-in Customer'}")
        lines.append("-" * 48)
        lines.append(f"{'Item':<20} {'Qty':>6} {'Price':>10} {'Total':>10}")
        lines.append("-" * 48)
        
        for item in sale.items.all():
            name = item.product_name[:20]
            lines.append(f"{name:<20} {item.quantity:>6.2f} {item.unit_price:>10.2f} {item.total:>10.2f}")
        
        lines.append("-" * 48)
        lines.append(f"{'Subtotal:':>38} {sale.subtotal:>10.2f}")
        
        if sale.discount_amount > 0:
            lines.append(f"{'Discount:':>38} -{sale.discount_amount:>9.2f}")
        
        if sale.loyalty_discount > 0:
            lines.append(f"{'Loyalty Discount:':>38} -{sale.loyalty_discount:>9.2f}")
        
        if sale.tax_amount > 0:
            lines.append(f"{'Tax (16%):':>38} {sale.tax_amount:>10.2f}")
        
        lines.append("=" * 48)
        lines.append(f"{'TOTAL:':>38} {sale.total:>10.2f}")
        lines.append(f"{'Amount Paid:':>38} {sale.amount_paid:>10.2f}")
        
        if sale.change_due > 0:
            lines.append(f"{'Change Due:':>38} {sale.change_due:>10.2f}")
        
        lines.append("=" * 48)
        
        if sale.loyalty_points_earned > 0:
            lines.append(f"Loyalty points earned: {sale.loyalty_points_earned}")
        
        lines.append("THANK YOU FOR SHOPPING WITH US!".center(48))
        lines.append("=" * 48)
        
        return "\n".join(lines)