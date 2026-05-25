from rest_framework.response import Response
from rest_framework.views import APIView
from .services.dashboard import get_dashboard_data
from .services.sales_reports import (
    get_sales_summary,
    get_sales_trend
)
from .services.product_reports import get_top_products
from .services.payment_reports import get_payment_summary
from .services.sales_reports import get_monthly_revenue_trend


class SalesSummaryView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        data = get_sales_summary(start_date, end_date)
        return Response(data)


class SalesTrendView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        data = get_sales_trend(start_date, end_date)
        return Response(data)
    
class DashboardView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        data = get_dashboard_data(start_date, end_date)

        return Response(data)
    
class TopProductsView(APIView):
    def get(self, request):

        limit = request.query_params.get("limit", 5)

        data = get_top_products(limit=int(limit))

        return Response(data)
    
class PaymentSummaryView(APIView):
    def get(self, request):

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        data = get_payment_summary(start_date, end_date)

        return Response(data)
    
class MonthlyRevenueTrendView(APIView):
    def get(self, request):
        data = get_monthly_revenue_trend()
        return Response(data)