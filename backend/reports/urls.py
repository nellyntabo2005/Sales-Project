from django.urls import path
from .views import SalesSummaryView, SalesTrendView, DashboardView, TopProductsView, PaymentSummaryView, MonthlyRevenueTrendView

urlpatterns = [
    path("sales-summary/", SalesSummaryView.as_view(), name="sales-summary"),
    path("sales-trend/", SalesTrendView.as_view(), name="sales-trend"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("top-products/", TopProductsView.as_view(), name="top-products"),
    path("payment-summary/", PaymentSummaryView.as_view(), name="payment-summary"),
    path("monthly-revenue/", MonthlyRevenueTrendView.as_view(),name="monthly-revenue"),
]