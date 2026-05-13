from django.db import models

from customers.models import Customer
from users.models import User
from products.models import Product


class Sale(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
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
        decimal_places=2
    )

    status = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale {self.id}"


class SaleItem(models.Model):

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.IntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.product.name