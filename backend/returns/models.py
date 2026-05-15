from django.db import models

from sales.models import Sale
from products.models import Product


class Return(models.Model):

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.IntegerField()

    reason = models.TextField()

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name
