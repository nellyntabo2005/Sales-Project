from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet
from .views import PaymentViewSet, ReceiptViewSet

router = DefaultRouter()
router.register(r'', PaymentViewSet)
router.register(r'receipts', ReceiptViewSet)


urlpatterns = router.urls