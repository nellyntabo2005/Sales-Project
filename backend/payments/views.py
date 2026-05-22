from rest_framework import viewsets
from .models import Payment
from .serializers import PaymentSerializer
from .serializers import PaymentSerializer, ReceiptSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer 
