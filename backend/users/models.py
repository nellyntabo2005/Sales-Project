from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('cashier', 'Cashier'),
        ('accountant', 'Accountant'),
        ('storekeeper', 'Storekeeper'),
        ('manager', 'Manager'),
    ]

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES
    )

    pin = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.username



    


class AuditLog(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    action = models.CharField(max_length=100)

    description = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action
