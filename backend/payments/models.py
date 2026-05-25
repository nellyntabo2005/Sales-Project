from django.db import models


class Payment(models.Model):

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mpesa', 'M-Pesa'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
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

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )

    payment_date = models.DateTimeField(auto_now_add=True)
    
    # M-Pesa specific fields
    mpesa_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="M-Pesa transaction ID"
    )
    
    mpesa_checkout_request_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Checkout request ID from STK push"
    )
    
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Customer phone number for M-Pesa"
    )

    def __str__(self):
        return f"Payment for Sale {self.sale_id} - {self.get_payment_method_display()}"


    