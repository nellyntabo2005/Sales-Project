# customers/serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    """
    Main serializer for Customer model.
    Handles data validation, creation, and updates.
    """
    
    # Read-only fields (API returns but client cannot modify)
    account_reference = serializers.CharField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)
    loyalty_points = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Computed field (not in database)
    discount_percentage = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id',
            'uuid',
            'account_reference',
            'name',
            'phone',
            'email',
            'address_line1',
            'address_line2',
            'city',
            'county',
            'postal_code',
            'tax_number',
            'loyalty_points',
            'total_spent',
            'pricing_tier',
            'is_active',
            'is_blacklisted',
            'notes',
            'created_at',
            'updated_at',
            'last_purchase_date',
            'discount_percentage',
            'full_address',
        ]
        read_only_fields = ['id', 'uuid', 'account_reference', 'loyalty_points', 
                           'total_spent', 'created_at', 'updated_at']
    
    def get_discount_percentage(self, obj):
        """Return customer's discount percentage"""
        return obj.get_discount_percentage()
    
    def get_full_address(self, obj):
        """Return formatted full address"""
        return obj.full_address
    
    def validate_phone(self, value):
        """Custom phone validation"""
        # Check if phone already exists (excluding current instance)
        instance = self.instance
        if Customer.objects.exclude(pk=instance.pk if instance else None).filter(phone=value).exists():
            raise serializers.ValidationError("A customer with this phone already exists.")
        return value
    
    def validate_email(self, value):
        """Custom email validation"""
        instance = self.instance
        if Customer.objects.exclude(pk=instance.pk if instance else None).filter(email=value).exists():
            raise serializers.ValidationError("A customer with this email already exists.")
        return value
    
    def create(self, validated_data):
        """Create new customer with any special handling"""
        return Customer.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update customer with any special handling"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CustomerLoyaltySerializer(serializers.ModelSerializer):
    """
    Simplified serializer for loyalty operations.
    Only exposes loyalty-related fields.
    """
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'loyalty_points', 'total_spent', 'pricing_tier']
        read_only_fields = ['id', 'name', 'phone', 'loyalty_points', 'total_spent']


class CustomerRedeemPointsSerializer(serializers.Serializer):
    """
    Serializer for redeeming loyalty points.
    """
    points_to_redeem = serializers.IntegerField(min_value=1, help_text="Number of points to redeem")
    
    def validate_points_to_redeem(self, value):
        """Ensure customer has enough points"""
        # This validation happens in the view where we have access to customer
        return value