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
