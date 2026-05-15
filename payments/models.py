from django.db import models
from sales.models import Sale


class Payment(models.Model):

    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Money'),
    )

    sale = models.OneToOneField(
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

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    payment_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        # get sale total
        total = self.sale.total

        # calculate change
        if self.amount_paid > total:
            self.change_given = self.amount_paid - total
        else:
            self.change_given = 0

        # mark sale as paid
        self.sale.status = "paid"
        self.sale.save()

        super().save(*args, **kwargs)

class Receipt(models.Model):

    sale = models.OneToOneField(Sale, on_delete=models.CASCADE)

    receipt_number = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number
   