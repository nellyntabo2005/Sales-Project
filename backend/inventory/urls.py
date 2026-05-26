# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BatchViewSet, StockMovementViewSet, PurchaseOrderViewSet,
    StockCountViewSet, StoreTransferViewSet, StoreStockViewSet,
    InventoryAlertViewSet, BulkInventoryViewSet
)

router = DefaultRouter()
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'stock-movements', StockMovementViewSet, basename='stock-movement')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'stock-counts', StockCountViewSet, basename='stock-count')
router.register(r'store-transfers', StoreTransferViewSet, basename='store-transfer')
router.register(r'store-stock', StoreStockViewSet, basename='store-stock')
router.register(r'inventory-alerts', InventoryAlertViewSet, basename='inventory-alert')
router.register(r'bulk', BulkInventoryViewSet, basename='bulk-inventory')
# Remove import-jobs router for now
# router.register(r'import-jobs', ImportJobViewSet, basename='import-job')

urlpatterns = [
    path('api/inventory/', include(router.urls)),
]