from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, SaleItemViewSet

router = DefaultRouter()
router.register(r'sales', SaleViewSet)
router.register(r'items', SaleItemViewSet)

urlpatterns = router.urls