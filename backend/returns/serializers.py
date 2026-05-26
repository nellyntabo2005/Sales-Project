# returns/serializers.py
from rest_framework import serializers
from .models import Return, ReturnItem
from products.serializers import ProductSerializer
from sales.serializers import SaleSerializer

class ReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    product_sku = serializers.SerializerMethodField()
    
    class Meta:
        model = ReturnItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'refund_amount', 'reason', 'condition'
        ]
    
    def get_product_name(self, obj):
        return obj.product.name
    
    def get_product_sku(self, obj):
        return obj.product.sku


class ReturnSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True, read_only=True)
    original_sale_details = SaleSerializer(source='original_sale', read_only=True)
    customer_name = serializers.SerializerMethodField()
    requested_by_name = serializers.SerializerMethodField()
    
    # Write-only for creating
    return_items = serializers.ListField(write_only=True, required=False)
    
    class Meta:
        model = Return
        fields = [
            'id', 'return_number', 'uuid', 'original_sale', 'original_sale_details',
            'customer', 'customer_name', 'reason', 'reason_description',
            'status', 'refund_amount', 'restocking_fee', 'net_refund',
            'refund_method', 'restock', 'notes', 'staff_notes',
            'requested_by', 'requested_by_name', 'approved_by', 'processed_by',
            'return_date', 'approved_at', 'processed_at',
            'items', 'return_items'
        ]
        read_only_fields = [
            'id', 'return_number', 'uuid', 'return_date', 'approved_at',
            'processed_at', 'net_refund'
        ]
    
    def get_customer_name(self, obj):
        return obj.customer.name
    
    def get_requested_by_name(self, obj):
        return obj.requested_by.get_full_name() or obj.requested_by.username
    
    def validate_refund_amount(self, value):
        #Ensure refund amount doesn't exceed sale total
        if self.instance and self.instance.original_sale:
            if value > self.instance.original_sale.total:
                raise serializers.ValidationError(
                    f"Refund amount cannot exceed sale total of {self.instance.original_sale.total}"
                )
        return value
    
    def create(self, validated_data):
        return_items = validated_data.pop('return_items', [])
        return_obj = Return.objects.create(**validated_data)
        
        for item in return_items:
            ReturnItem.objects.create(return_obj=return_obj, **item)
        
        return return_obj