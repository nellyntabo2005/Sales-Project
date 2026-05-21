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

    stock_quantity = models.IntegerField(default=0)

    reserved_stock = models.IntegerField(default=0)

    def available_stock(self):
        return self.stock_quantity - self.reserved_stock

    def __str__(self):
        return self.name
