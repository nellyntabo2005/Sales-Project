from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from urllib3 import request
from .models import Sale, SaleItem
from .models import Sale
from .serializers import SaleSerializer

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Sale, SaleItem, Receipt
from products.models import Product
from payments.models import Payment
from users.models import AuditLog

from notifications.utils import send_notification

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer 

class POSCheckoutView(APIView):

    @transaction.atomic
    def post(self, request):

        data = request.data

        # 1. CREATE SALE (ONLY ONCE)
        sale = Sale.objects.create(
            customer_id=data['customer_id'],
            user_id=data['user_id'],
            subtotal=data['subtotal'],
            discount=data.get('discount', 0),
            tax=data.get('tax', 0),
            total=data['total'],
            status="pending"
        )

        items = data['items']

        # 2. RESERVE STOCK + CREATE SALE ITEMS
        for item in items:

            product = Product.objects.get(id=item['product_id'])

            available_stock = product.stock_quantity - product.reserved_stock

            if available_stock < item['quantity']:
                raise ValidationError(f"Not enough stock for {product.name}")

            product.reserved_stock += item['quantity']
            product.save()

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=item['quantity'],
                unit_price=item['unit_price']
            )

        # 3. CREATE PAYMENT (ONCE)
        payment = Payment.objects.create(
            sale=sale,
            amount_paid=data['amount_paid'],
            change_given=data.get('change_given', 0),
            payment_method=data['payment_method']
        )

        # 4. FINALIZE STOCK AFTER PAYMENT
        for item in items:

            product = Product.objects.get(id=item['product_id'])

            product.stock_quantity -= item['quantity']
            product.reserved_stock -= item['quantity']

            product.save()

        # 5. CREATE RECEIPT
        receipt = Receipt.objects.create(payment=payment)
        send_notification(request.user, f"🛒 POS completed: Sale #{sale.id}, Receipt #{receipt.receipt_number}")

        # 6. AUDIT LOG
        AuditLog.objects.create(
            user=sale.user,
            action="POS_CHECKOUT",
            description=f"Sale {sale.id} completed with receipt {receipt.receipt_number}"
        )

        return Response({
            "message": "Transaction successful",
            "sale_id": sale.id,
            "receipt_number": receipt.receipt_number

        
        }, status=status.HTTP_201_CREATED)
       
    def perform_create(self, serializer):
        sale = serializer.save()
        send_notification(request.user, f"🛒 New sale created: Sale ID {sale.id} for customer {sale.customer.name} with total KES{sale.total}")

    
