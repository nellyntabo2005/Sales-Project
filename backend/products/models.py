from django.db import models


class Product(models.Model):

    name = models.CharField(max_length=150)

    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    

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
    

class Supplier(models.Model):

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    
    def __str__(self):
        return self.name