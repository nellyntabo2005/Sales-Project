<<<<<<< HEAD
# reports/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, SavedReportViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'saved-reports', SavedReportViewSet, basename='saved-report')
# Remove exports router if causing issues
# router.register(r'exports', ReportExportViewSet, basename='report-export')

urlpatterns = [
    path('api/reports/', include(router.urls)),
=======
from django.urls import path
from .views import SalesSummaryView, SalesTrendView, DashboardView, TopProductsView, PaymentSummaryView, MonthlyRevenueTrendView

urlpatterns = [
    path("sales-summary/", SalesSummaryView.as_view(), name="sales-summary"),
    path("sales-trend/", SalesTrendView.as_view(), name="sales-trend"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("top-products/", TopProductsView.as_view(), name="top-products"),
    path("payment-summary/", PaymentSummaryView.as_view(), name="payment-summary"),
    path("monthly-revenue/", MonthlyRevenueTrendView.as_view(),name="monthly-revenue"),
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
]