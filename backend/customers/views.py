# customers/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Customer
<<<<<<< HEAD
from .serializers import (
    CustomerSerializer, 
    CustomerLoyaltySerializer, 
    CustomerRedeemPointsSerializer
)
=======
from .serializers import CustomerSerializer
from notifications.utils import send_notification
from urllib3 import request

>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d

class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Customer CRUD operations.
    Provides: list, create, retrieve, update, partial_update, destroy
    
    Additional actions:
    - redeem_points: Redeem loyalty points
    - add_points: Manually add loyalty points
    - loyalty_info: Get loyalty summary
    """
    
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
<<<<<<< HEAD
    permission_classes = [IsAuthenticated]
    
    # Filtering, searching, ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_blacklisted', 'pricing_tier']
    search_fields = ['name', 'phone', 'email', 'account_reference']
    ordering_fields = ['name', 'created_at', 'total_spent', 'loyalty_points']
    ordering = ['-created_at']  # Default ordering
    
    def get_serializer_class(self):
        """Return different serializers based on action"""
        if self.action == 'loyalty_info':
            return CustomerLoyaltySerializer
        return CustomerSerializer
    
    @action(detail=True, methods=['post'], url_path='redeem-points')
    def redeem_points(self, request, pk=None):
        """
        POST /api/customers/{id}/redeem-points/
        Body: {"points_to_redeem": 100}
        
        Redeems customer loyalty points for discount.
        Returns the monetary value of redeemed points.
        """
        customer = self.get_object()
        serializer = CustomerRedeemPointsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        points_to_redeem = serializer.validated_data['points_to_redeem']
        
        # Check if customer has enough points
        if points_to_redeem > customer.loyalty_points:
            return Response(
                {"error": f"Insufficient points. You have {customer.loyalty_points} points."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            customer.redeem_loyalty_points(points_to_redeem)
            
            # Calculate discount value (1 point = 1 KES discount)
            discount_value = points_to_redeem
            
            return Response({
                "message": f"Successfully redeemed {points_to_redeem} points",
                "points_remaining": customer.loyalty_points,
                "discount_value_kes": discount_value,
                "customer": CustomerLoyaltySerializer(customer).data
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='add-points')
    def add_points(self, request, pk=None):
        """
        POST /api/customers/{id}/add-points/
        Body: {"points": 50}
        
        Manually adds loyalty points (e.g., for promotions).
        """
        customer = self.get_object()
        points = request.data.get('points', 0)
        
        try:
            points = int(points)
            if points <= 0:
                return Response(
                    {"error": "Points must be a positive integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            customer.add_loyalty_points(points)
            
            return Response({
                "message": f"Added {points} loyalty points",
                "points_remaining": customer.loyalty_points,
                "customer": CustomerLoyaltySerializer(customer).data
            }, status=status.HTTP_200_OK)
            
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid points value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='loyalty-info')
    def loyalty_info(self, request, pk=None):
        """
        GET /api/customers/{id}/loyalty-info/
        
        Returns customer loyalty summary for POS display.
        """
        customer = self.get_object()
        serializer = CustomerLoyaltySerializer(customer)
        
        # Add computed values
        data = serializer.data
        data['discount_percentage'] = customer.get_discount_percentage()
        data['points_to_kes_rate'] = "1 point = 1 KES"
        
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='search-by-phone')
    def search_by_phone(self, request):
        """
        GET /api/customers/search-by-phone/?phone=0712345678
        
        Quick customer lookup by phone (for POS).
        """
        phone = request.query_params.get('phone', None)
        
        if not phone:
            return Response(
                {"error": "Phone parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            customer = Customer.objects.get(phone=phone, is_active=True)
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='top-customers')
    def top_customers(self, request):
        """
        GET /api/customers/top-customers/?limit=10
        
        Returns top-spending customers.
        """
        limit = int(request.query_params.get('limit', 10))
        top_customers = Customer.objects.filter(is_active=True).order_by('-total_spent')[:limit]
        serializer = CustomerSerializer(top_customers, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Override delete to soft-delete by setting is_active=False
        """
        customer = self.get_object()
        customer.is_active = False
        customer.save()
        return Response(
            {"message": f"Customer {customer.name} has been deactivated"},
            status=status.HTTP_200_OK
        )
=======

# notifications for new customers
    def perform_create(self, serializer):
        customer = serializer.save()
        send_notification(request.user, f"👤 New customer added: {customer.name}")


>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
