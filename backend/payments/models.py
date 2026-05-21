from django.db import models


class Payment(models.Model):

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mpesa', 'M-Pesa'),
    ]

    sale = models.ForeignKey(
        'sales.Sale',
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

    def __str__(self):
        return f"Payment for Sale {self.sale_id}"



        
    