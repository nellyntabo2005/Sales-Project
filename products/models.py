from django.db import models


class Product(models.Model):

    name = models.CharField(max_length=150)

    sku = models.CharField(
        max_length=50,
        unique=True
    )

    barcode = models.CharField(
        max_length=100,
        unique=True
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock_quantity = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
