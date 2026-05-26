# payments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentAccountViewSet,
    PaymentTransactionViewSet,
    MpesaAccountViewSet,
    MpesaTransactionViewSet,
    MpesaPaymentViewSet,
    ExpenseCategoryViewSet,
    ExpenseViewSet
)

router = DefaultRouter()
<<<<<<< HEAD
router.register(r'accounts', PaymentAccountViewSet, basename='payment-account')
router.register(r'transactions', PaymentTransactionViewSet, basename='payment-transaction')
router.register(r'mpesa-accounts', MpesaAccountViewSet, basename='mpesa-account')
router.register(r'mpesa-transactions', MpesaTransactionViewSet, basename='mpesa-transaction')
router.register(r'mpesa-payments', MpesaPaymentViewSet, basename='mpesa-payment')
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', ExpenseViewSet, basename='expense')

urlpatterns = [
    path('api/', include(router.urls)),
]
=======
router.register(r'', PaymentViewSet, basename='payment')


urlpatterns = router.urls
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
