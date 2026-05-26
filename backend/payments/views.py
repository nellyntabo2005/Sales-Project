from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
<<<<<<< HEAD
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
import pandas as pd
import io

from .models import (
    PaymentAccount, 
    PaymentTransaction, 
    MpesaAccount, 
    MpesaTransaction,
    MpesaCallbackLog,
    ExpenseCategory,
    Expense
)
from .serializers import (
    PaymentAccountSerializer,
    PaymentTransactionSerializer,
    MpesaAccountSerializer,
    MpesaTransactionSerializer,
    MpesaStkPushSerializer,
    MpesaQueryStatusSerializer,
    ExpenseCategorySerializer,      # ADD THIS - was missing
    ExpenseSerializer               # ADD THIS - was missing
)
from .mpesa_service import MpesaService, MpesaCallbackHandler


class PaymentAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payment accounts (cash, bank, M-Pesa)"""
    
    queryset = PaymentAccount.objects.all()
    serializer_class = PaymentAccountSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['account_type', 'is_active', 'is_default']
    search_fields = ['name', 'account_number', 'bank_name']
    ordering_fields = ['name', 'current_balance']
    ordering = ['account_type', 'name']
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['super_admin', 'admin', 'accountant']:
            return PaymentAccount.objects.all()
        return PaymentAccount.objects.filter(is_active=True)


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payment transactions (read-only)"""
    
    queryset = PaymentTransaction.objects.all()
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'payment_method', 'status']
    search_fields = ['transaction_id', 'reference_number', 'description']
    ordering_fields = ['transaction_date', 'amount']
    ordering = ['-transaction_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['super_admin', 'admin', 'accountant']:
            return PaymentTransaction.objects.all()
        return PaymentTransaction.objects.filter(recorded_by=user)
    
    @action(detail=False, methods=['get'], url_path='summary')
    def transaction_summary(self, request):
        """Get summary of transactions for a period"""
        from django.db.models import Sum, Count
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.get_queryset()
        
        if start_date:
            queryset = queryset.filter(transaction_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__date__lte=end_date)
        
        summary = {
            'total_income': queryset.filter(
                transaction_type__in=['sale', 'deposit']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'total_expenses': queryset.filter(
                transaction_type__in=['expense', 'supplier_payment', 'salary', 'withdrawal']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'total_fees': queryset.aggregate(total=Sum('fee'))['total'] or Decimal('0'),
            'total_tax': queryset.aggregate(total=Sum('tax'))['total'] or Decimal('0'),
            'transaction_count': queryset.count(),
            'by_type': list(queryset.values('transaction_type').annotate(
                total=Sum('amount'),
                count=Count('id')
            ))
        }
        
        return Response(summary)


class MpesaAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for M-Pesa account management"""
    
    queryset = MpesaAccount.objects.all()
    serializer_class = MpesaAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role in ['super_admin', 'admin']:
            return MpesaAccount.objects.all()
        return MpesaAccount.objects.filter(is_active=True)
    
    @action(detail=False, methods=['post'], url_path='set-default')
    def set_default(self, request):
        """Set default M-Pesa account"""
        account_id = request.data.get('account_id')
        try:
            account = MpesaAccount.objects.get(id=account_id)
            MpesaAccount.objects.filter(is_default=True).update(is_default=False)
            account.is_default = True
            account.save()
            return Response({'message': 'Default account set successfully'})
        except MpesaAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)


class MpesaTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing M-Pesa transactions"""
    
    queryset = MpesaTransaction.objects.all()
    serializer_class = MpesaTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'transaction_type', 'phone_number']
    search_fields = ['mpesa_receipt_number', 'checkout_request_id', 'account_reference']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']


class MpesaPaymentViewSet(viewsets.GenericViewSet):
    """ViewSet for M-Pesa payment operations"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='stk-push')
    def initiate_stk_push(self, request):
        """Initiate M-Pesa STK Push payment"""
        serializer = MpesaStkPushSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            mpesa_service = MpesaService()
            
            result = mpesa_service.stk_push(
                phone_number=data['phone_number'],
                amount=data['amount'],
                account_reference=data['account_reference'],
                transaction_desc=data.get('transaction_desc', 'Payment for goods')
            )
            
            if result['success'] and data.get('sale_id'):
                from sales.models import Sale
                try:
                    sale = Sale.objects.get(id=data['sale_id'])
                    transaction = MpesaTransaction.objects.get(id=result['transaction_id'])
                    transaction.sale = sale
                    transaction.save()
                except Sale.DoesNotExist:
                    pass
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='query')
    def query_transaction(self, request):
        """Query STK Push transaction status"""
        serializer = MpesaQueryStatusSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        checkout_request_id = serializer.validated_data['checkout_request_id']
        
        try:
            mpesa_service = MpesaService()
            result = mpesa_service.query_status(checkout_request_id)
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='callback')
    def mpesa_callback(self, request):
        """M-Pesa callback endpoint (public, no auth required)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0]
        else:
            client_ip = request.META.get('REMOTE_ADDR')
        
        success, message = MpesaCallbackHandler.handle_stk_push_callback(
            request.data, client_ip
        )
        
        if success:
            return Response({'ResultCode': 0, 'ResultDesc': 'Success'})
        else:
            return Response({'ResultCode': 1, 'ResultDesc': message})


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for expense categories"""
    
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer  # Now this is defined
    permission_classes = [IsAuthenticated]
    
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for expenses"""
    
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer  # Now this is defined
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'status', 'expense_date']
    search_fields = ['expense_number', 'description']
    ordering_fields = ['expense_date', 'amount']
    ordering = ['-expense_date']
    
    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve_expense(self, request, pk=None):
        """Approve an expense"""
        expense = self.get_object()
        
        if request.user.role not in ['super_admin', 'admin', 'manager']:
            return Response(
                {"error": "Only managers can approve expenses"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if expense.status != 'submitted':
            return Response(
                {"error": f"Cannot approve expense with status: {expense.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expense.status = 'approved'
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save()
        
        return Response({'message': 'Expense approved'})
    
    @action(detail=True, methods=['post'], url_path='pay')
    def pay_expense(self, request, pk=None):
        """Mark expense as paid"""
        expense = self.get_object()
        
        if expense.status != 'approved':
            return Response(
                {"error": f"Cannot pay expense with status: {expense.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from_account_id = request.data.get('from_account_id')
        if not from_account_id:
            return Response(
                {"error": "from_account_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from_account = PaymentAccount.objects.get(id=from_account_id, is_active=True)
        except PaymentAccount.DoesNotExist:
            return Response(
                {"error": "Payment account not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        payment_transaction = PaymentTransaction.objects.create(
            transaction_type='expense',
            payment_method='cash' if from_account.account_type == 'cash' else 'bank_transfer',
            amount=expense.total_amount,
            from_account=from_account,
            reference_number=expense.expense_number,
            description=expense.description,
            recorded_by=request.user,
            status='completed'
        )
        
        expense.payment_transaction = payment_transaction
        expense.status = 'paid'
        expense.paid_at = timezone.now()
        expense.save()
        
        return Response({
            'message': 'Expense paid',
            'payment_transaction_id': payment_transaction.transaction_id
        })
=======
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
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
