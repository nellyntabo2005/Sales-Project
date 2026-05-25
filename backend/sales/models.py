from django.db import models
from customers.models import Customer
from products.models import Product
from users.models import User
from users.models import AuditLog
import uuid


class Sale(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale {self.id}"


class SaleItem(models.Model):

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        self.product.stock_quantity -= self.quantity
        self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product.name


class Receipt(models.Model):

    payment = models.OneToOneField(
        'payments.Payment',
        on_delete=models.CASCADE,
        related_name="receipt"
    )

    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True
    )

    printed_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        if not self.receipt_number:
            self.receipt_number = str(uuid.uuid4()).split('-')[0].upper()

        super().save(*args, **kwargs)

        if is_new:
            AuditLog.objects.create(
                user=self.payment.sale.user,
                action="RECEIPT_CREATED",
                description=f"Receipt {self.receipt_number} created for Sale {self.payment.sale.id}"
            )

    def __str__(self):
        return self.receipt_number