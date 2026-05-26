from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Payment
from .serializers import PaymentSerializer


from notifications.utils import send_notification
from django_daraja.mpesa.core import MpesaClient
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer 

    def perform_create(self, serializer):
        payment = serializer.save()
        send_notification(payment.sale.user, f"💰 New payment received: KES{payment.amount_paid} from {payment.sale.customer.name}")

    @action(detail=False, methods=['post'])
    def initiate_mpesa_payment(self, request):
        """Initiate M-Pesa STK Push for payment"""
        try:
            phone_number = request.data.get('phone_number')
            amount = request.data.get('amount')
            payment_id = request.data.get('payment_id')
            
            if not all([phone_number, amount, payment_id]):
                return Response(
                    {'error': 'Missing required fields: phone_number, amount, payment_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            payment = get_object_or_404(Payment, id=payment_id)
            
            
            cl = MpesaClient()
            
            
            response = cl.stk_push(
                phone_number=phone_number,
                amount=int(amount),
                account_reference=f"SALE-{payment.sale.id}",
                transaction_desc=f"Payment for Sale {payment.sale.id}",
                callback_url=settings.MPESA_CALLBACK_URL
            )
            
            
            if response and 'CheckoutRequestID' in response:
                payment.mpesa_checkout_request_id = response['CheckoutRequestID']
                payment.phone_number = phone_number
                payment.save()
                
                return Response({
                    'success': True,
                    'message': 'STK push initiated successfully',
                    'checkout_request_id': response['CheckoutRequestID']
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"M-Pesa STK Push failed: {response}")
                return Response(
                    {'error': 'Failed to initiate payment', 'details': response},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.exception(f"Error initiating M-Pesa payment: {str(e)}")
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def mpesa_callback(self, request):
        """Handle M-Pesa payment callback"""
        try:
            data = request.data
            logger.info(f"M-Pesa Callback received: {data}")
            
            
            body = data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc', '')
            
            
            payment = get_object_or_404(Payment, mpesa_checkout_request_id=checkout_request_id)
            
            if result_code == 0:  
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                mpesa_receipt_number = None
                for item in items:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_receipt_number = item.get('Value')
                    
                payment.mpesa_transaction_id = mpesa_receipt_number
                payment.payment_status = 'completed'
                payment.save()

                send_notification(
                    payment.sale.user,
                    f"✅ M-Pesa payment confirmed: KES{payment.amount_paid} (Ref: {mpesa_receipt_number})"
                )
                
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
            else:  # Failed
                payment.payment_status = 'failed'
                payment.save()
                
                send_notification(
                    payment.sale.user,
                    f"❌ M-Pesa payment failed: {result_desc}"
                )
                
                return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})
                
        except Exception as e:
            logger.exception(f"Error processing M-Pesa callback: {str(e)}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'}, status=500)

    @action(detail=False, methods=['post'])
    def query_mpesa_payment(self, request):
        """Query M-Pesa payment status"""
        try:
            checkout_request_id = request.data.get('checkout_request_id')
            
            if not checkout_request_id:
                return Response(
                    {'error': 'checkout_request_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cl = MpesaClient()
            
            # Query payment status
            response = cl.query_payment_status(
                checkout_request_id=checkout_request_id
            )
            
            return Response(response, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Error querying M-Pesa payment: {str(e)}")
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
