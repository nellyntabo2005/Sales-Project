from rest_framework import viewsets
from .models import Payment
from .serializers import PaymentSerializer
from .models import Payment, Receipt
from .serializers import PaymentSerializer, ReceiptSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    serializer_class = ReceiptSerializer

class ReceiptViewSet(viewsets.ModelViewSet):

    queryset = Receipt.objects.all()

    serializer_class = ReceiptSerializer