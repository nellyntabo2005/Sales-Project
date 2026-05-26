# products/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import Category, Supplier, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Product Categories
    """
    full_path = serializers.SerializerMethodField()
    level = serializers.IntegerField(read_only=True)
    children_count = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'icon', 'color', 'is_active', 'full_path', 'level',
            'children_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_full_path(self, obj):
        return obj.get_full_path() if hasattr(obj, 'get_full_path') else obj.name
    
    def get_children_count(self, obj):
        return obj.children.filter(is_active=True).count() if hasattr(obj, 'children') else 0
    
    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None


class SupplierSerializer(serializers.ModelSerializer):
    """
    Serializer for Product Suppliers
    """
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'contact_person', 'phone', 'email',
            'website', 'address_line1', 'address_line2', 'city', 'county',
            'postal_code', 'tax_number', 'bank_name', 'bank_account',
            'is_active', 'is_preferred', 'payment_terms', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for Product Images
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'caption', 'is_primary', 'order']
        read_only_fields = ['id']
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None



class ProductSerializer(serializers.ModelSerializer):
    """
    Main serializer for Products
    """
    # Nested serializers for detailed views
    category_name = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    #batches = BatchSerializer(many=True, read_only=True)
    
    # Computed fields
    profit_margin = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_value = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    
    class Meta:
        model = Product
        fields = [
            'id', 'uuid', 'sku', 'barcode', 'name', 'description',
            'category', 'category_name', 'supplier', 'supplier_name', 'supplier_sku',
            'cost_price', 'retail_price', 'wholesale_price', 'carton_price', 'carton_quantity',
            'stock_quantity', 'reorder_level', 'reorder_quantity', 'minimum_stock', 'maximum_stock',
            'unit', 'tax_rate', 'weight', 'length', 'width', 'height',
            'is_active', 'is_featured', 'is_digital', 'main_image',
            'profit_margin', 'is_low_stock', 'stock_value',
            'notes', 'created_at', 'updated_at', 'last_purchased_at',
            'images', 'batches'
        ]
        read_only_fields = [
            'id', 'uuid', 'sku', 'created_at', 'updated_at', 
            'profit_margin', 'is_low_stock', 'stock_value'
        ]
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    
    def get_supplier_name(self, obj):
        return obj.supplier.name if obj.supplier else None
    
    def validate_retail_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Retail price must be greater than zero")
        return value
    
    def validate_wholesale_price(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("Wholesale price must be greater than zero")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Ensure wholesale price is less than retail price
        if 'wholesale_price' in data and data.get('wholesale_price'):
            retail = data.get('retail_price', getattr(self.instance, 'retail_price', None))
            if retail and data['wholesale_price'] >= retail:
                raise serializers.ValidationError({
                    'wholesale_price': "Wholesale price must be less than retail price"
                })
        return data


class ProductImportSerializer(serializers.Serializer):
    """
    Serializer for bulk product import via Excel/CSV
    """
    file = serializers.FileField()
    
    def validate_file(self, value):
        """Validate file type"""
        if not value.name.endswith(('.xlsx', '.xls', '.csv')):
            raise serializers.ValidationError("File must be Excel or CSV format")
        
        # Validate file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB")
        
        return value


class BulkPriceUpdateSerializer(serializers.Serializer):
    """
    Serializer for bulk price updates
    """
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of product IDs. If empty, applies to all"
    )
    category_id = serializers.IntegerField(required=False, help_text="Update by category")
    supplier_id = serializers.IntegerField(required=False, help_text="Update by supplier")
    update_type = serializers.ChoiceField(choices=['percentage', 'fixed'])
    adjustment = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_field = serializers.ChoiceField(
        choices=['retail_price', 'wholesale_price', 'cost_price'],
        default='retail_price'
    )
    
    def validate(self, data):
        """Ensure either product_ids or category_id or supplier_id is provided"""
        if not data.get('product_ids') and not data.get('category_id') and not data.get('supplier_id'):
            raise serializers.ValidationError(
                "Either product_ids, category_id, or supplier_id must be provided"
            )
        return data


class ProductStockUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating product stock
    """
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    operation = serializers.ChoiceField(choices=['set', 'add', 'subtract'], default='add')
    reason = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ProductSearchSerializer(serializers.Serializer):
    """
    Serializer for product search filters
    """
    q = serializers.CharField(required=False, allow_blank=True)
    category = serializers.IntegerField(required=False)
    supplier = serializers.IntegerField(required=False)
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    in_stock = serializers.BooleanField(required=False)
    low_stock = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False, default=True)
    sort_by = serializers.ChoiceField(
        choices=['name', 'retail_price', 'stock_quantity', 'created_at'],
        required=False,
        default='name'
    )
    sort_order = serializers.ChoiceField(
        choices=['asc', 'desc'],
        required=False,
        default='asc'
    )