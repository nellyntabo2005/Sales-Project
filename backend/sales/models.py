from django.db import models
from customers.models import Customer
from products.models import Product
from users.models import User


# =========================
# SALE (Main Transaction)
# =========================
class Sale(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_total(self):
        total_items = sum(item.subtotal for item in self.items.all())

        self.subtotal = total_items
        self.total = total_items - self.discount + self.tax

        self.save()


# =========================
# SALE ITEMS (Products in Sale)
# =========================
class SaleItem(models.Model):

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.IntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def save(self, *args, **kwargs):
        # calculate subtotal
        self.subtotal = self.quantity * self.unit_price

        # reduce stock
        self.product.stock_quantity -= self.quantity
        self.product.save()

        super().save(*args, **kwargs)