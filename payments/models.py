from django.db import models

from sales.models import Sale


class Payment(models.Model):

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    change_given = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_method = models.CharField(max_length=20)

    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_method


class Receipt(models.Model):

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE
    )

    receipt_number = models.CharField(
        max_length=50,
        unique=True
    )

    printed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number
