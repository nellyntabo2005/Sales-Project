from rest_framework import serializers
from .models import Payment
from .models import Payment, Receipt


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'

class ReceiptSerializer(serializers.ModelSerializer):

    class Meta:
        model = Receipt
        fields = '__all__'