from django.db import models


class Customer(models.Model):

    name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20)

    account_reference = models.CharField(
        max_length=50,
        unique=True
    )

    email = models.EmailField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class loyalty_points(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='loyalty_points'
    )

    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.customer.name} - {self.points} points"
    
