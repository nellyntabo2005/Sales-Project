from rest_framework import viewsets
from .models import Payment
from .serializers import PaymentSerializer
from .serializers import PaymentSerializer, ReceiptSerializer

from notifications.utils import send_notification
from urllib3 import request


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer 

# notifications for payments, refunds and failures
    def perform_create(self, serializer):
        payment = serializer.save()
        send_notification(request.user, f"💰 New payment received: KES{payment.amount} from {payment.customer.name}")

    def perform_create_failure(self, serializer):
        send_notification(request.user, f"❌ Payment failed for {serializer.validated_data.get('customer').name} with amount ${serializer.validated_data.get('amount')}")
        return serializer.save()

    def perform_refund(self, serializer):
        payment = serializer.save()
        send_notification(request.user, f"💸 Payment refunded: KES{payment.amount} to {payment.customer.name}")
        return payment