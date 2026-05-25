from rest_framework import viewsets
from .models import Customer
from .serializers import CustomerSerializer
from notifications.utils import send_notification
from urllib3 import request


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

# notifications for new customers
    def perform_create(self, serializer):
        customer = serializer.save()
        send_notification(request.user, f"👤 New customer added: {customer.name}")


