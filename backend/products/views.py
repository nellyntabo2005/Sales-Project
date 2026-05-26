# products/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
<<<<<<< HEAD
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
import pandas as pd
import io
import json
from datetime import datetime

from .models import Category, Supplier, Product, ProductImage  # Removed Batch
from .serializers import (
    CategorySerializer, SupplierSerializer, ProductSerializer,
    ProductImageSerializer, ProductImportSerializer,
    BulkPriceUpdateSerializer
)

# If you need Batch, import from inventory:
# from inventory.models import Batch
# from inventory.serializers import BatchSerializer


# Rest of your views continue...
# Remove or comment out any BatchViewSet in this file since it belongs in inventory

from .models import Category, Supplier, Product, ProductImage
from .serializers import (
    CategorySerializer, SupplierSerializer, ProductSerializer,
    ProductImageSerializer,  ProductImportSerializer,
    BulkPriceUpdateSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product Categories
    Supports nested categories (parent-child hierarchy)
    """
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'], url_path='products')
    def get_category_products(self, request, pk=None):
        """
        GET /api/categories/{id}/products/
        
        Get all products in this category (including subcategories)
        """
        category = self.get_object()
        
        # Get all subcategory IDs
        category_ids = [category.id]
        subcategories = category.children.filter(is_active=True)
        
        for subcat in subcategories:
            category_ids.append(subcat.id)
            category_ids.extend([c.id for c in subcat.children.filter(is_active=True)])
        
        products = Product.objects.filter(
            category_id__in=category_ids,
            is_active=True
        )
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='tree')
    def category_tree(self, request):
        """
        GET /api/categories/tree/
        
        Get category hierarchy tree
        """
        root_categories = Category.objects.filter(parent=None, is_active=True)
        
        def build_tree(category):
            return {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'icon': category.icon,
                'color': category.color,
                'children': [build_tree(child) for child in category.children.filter(is_active=True)]
            }
        
        tree = [build_tree(cat) for cat in root_categories]
        return Response(tree)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product Suppliers/Vendors
    """
    
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_preferred', 'city', 'county']
    search_fields = ['name', 'code', 'phone', 'email', 'contact_person']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'], url_path='products')
    def get_supplier_products(self, request, pk=None):
        """
        GET /api/suppliers/{id}/products/
        
        Get all products from this supplier
        """
        supplier = self.get_object()
        products = Product.objects.filter(supplier=supplier, is_active=True)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import_suppliers(self, request):
        """
        POST /api/suppliers/bulk-import/
        
        Import suppliers from Excel/CSV
        """
        file = request.FILES.get('file')
        
        if not file:
            return Response(
                {"error": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            created_count = 0
            updated_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    name = str(row.get('name', '')).strip()
                    if not name:
                        errors.append(f"Row {index + 2}: Supplier name is required")
                        continue
                    
                    supplier, created = Supplier.objects.update_or_create(
                        name=name,
                        defaults={
                            'contact_person': str(row.get('contact_person', '')) if pd.notna(row.get('contact_person')) else '',
                            'phone': str(row.get('phone', '')) if pd.notna(row.get('phone')) else '',
                            'email': str(row.get('email', '')) if pd.notna(row.get('email')) else '',
                            'address_line1': str(row.get('address', '')) if pd.notna(row.get('address')) else '',
                            'city': str(row.get('city', '')) if pd.notna(row.get('city')) else '',
                            'county': str(row.get('county', '')) if pd.notna(row.get('county')) else '',
                            'is_preferred': str(row.get('is_preferred', 'No')).lower() == 'yes',
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            return Response({
                'message': 'Import completed',
                'created': created_count,
                'updated': updated_count,
                'errors': errors[:20]  # First 20 errors
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to read file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], url_path='export')
    def export_suppliers(self, request):
        """
        GET /api/suppliers/export/
        
        Export suppliers to Excel
        """
        suppliers = self.get_queryset().filter(is_active=True)
        
        data = []
        for supplier in suppliers:
            data.append({
                'Code': supplier.code,
                'Name': supplier.name,
                'Contact Person': supplier.contact_person,
                'Phone': supplier.phone,
                'Email': supplier.email,
                'City': supplier.city,
                'County': supplier.county,
                'Preferred': 'Yes' if supplier.is_preferred else 'No',
                'Payment Terms': f"{supplier.payment_terms} days",
                'Created': supplier.created_at.strftime('%Y-%m-%d') if supplier.created_at else '',
            })
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Suppliers', index=False)
        
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="suppliers_export.xlsx"'
        
        return response

=======
from users.permissions import IsAdmin
from notifications.utils import send_notification
from urllib3 import request
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Products with POS-specific actions and bulk operations
    """
    
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
<<<<<<< HEAD
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'supplier', 'is_active', 'is_featured', 'unit', 'tax_rate']
    search_fields = ['name', 'sku', 'barcode', 'description']
    ordering_fields = ['name', 'retail_price', 'stock_quantity', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """
        Filter queryset based on user role and query params
        """
        queryset = super().get_queryset()
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__lte=F('reorder_level')).exclude(reorder_level=0)
        
        # Filter by category tree
        category_id = self.request.query_params.get('category_tree')
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                category_ids = [category.id]
                for child in category.children.all():
                    category_ids.append(child.id)
                queryset = queryset.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='low-stock')
    def low_stock_products(self, request):
        """
        GET /api/products/low-stock/
        
        Get products that need reordering
        """
        low_stock = Product.objects.filter(
            is_active=True,
            stock_quantity__lte=F('reorder_level')
        ).exclude(reorder_level=0)
        
        # Add urgency level
        results = []
        for product in low_stock:
            serializer = self.get_serializer(product)
            data = serializer.data
            # Calculate urgency
            if product.stock_quantity == 0:
                urgency = 'critical'
            elif product.stock_quantity <= product.reorder_level / 2:
                urgency = 'high'
            else:
                urgency = 'medium'
            data['urgency'] = urgency
            results.append(data)
        
        return Response({
            'count': low_stock.count(),
            'results': results
        })
    
    @action(detail=False, methods=['get'], url_path='by-barcode')
    def get_by_barcode(self, request):
        """
        GET /api/products/by-barcode/?barcode=1234567890123
        
        Quick product lookup by barcode (for POS scanner)
        Returns product with stock info
        """
        barcode = request.query_params.get('barcode')
        
        if not barcode:
            return Response(
                {"error": "barcode parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(barcode=barcode, is_active=True)
            serializer = self.get_serializer(product)
            data = serializer.data
            
            # Add stock status for POS
            if product.stock_quantity <= 0:
                data['stock_status'] = 'out_of_stock'
            elif product.stock_quantity <= product.reorder_level:
                data['stock_status'] = 'low_stock'
            else:
                data['stock_status'] = 'in_stock'
            
            return Response(data)
        except Product.DoesNotExist:
            # Try by SKU as fallback
            try:
                product = Product.objects.get(sku=barcode, is_active=True)
                serializer = self.get_serializer(product)
                return Response(serializer.data)
            except Product.DoesNotExist:
                return Response(
                    {"error": "Product not found", "barcode": barcode},
                    status=status.HTTP_404_NOT_FOUND
                )
    
    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        """
        POST /api/products/bulk-import/
        
        Import products from Excel/CSV file
        Supports: .xlsx, .xls, .csv
        
        Required columns: name, cost_price, retail_price, stock_quantity, unit, tax_rate
        Optional columns: sku, barcode, category, supplier, wholesale_price, reorder_level, description
        """
        file = request.FILES.get('file')
        
        if not file:
            return Response(
                {"error": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File size must be less than 10MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file extension
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        if not any(file.name.endswith(ext) for ext in allowed_extensions):
            return Response(
                {"error": f"File must be one of: {', '.join(allowed_extensions)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, dtype=str)
            else:
                df = pd.read_excel(file, dtype=str)
            
            # Clean up column names
            df.columns = df.columns.str.lower().str.strip()
            
            # Required columns validation
            required_cols = ['name', 'cost_price', 'retail_price', 'stock_quantity', 'unit', 'tax_rate']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return Response(
                    {"error": f"Missing required columns: {', '.join(missing_cols)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Statistics
            total_rows = len(df)
            successful = 0
            failed = 0
            errors = []
            
            # Progress tracking (for large files)
            from .models import BulkImportJob
            import_job = BulkImportJob.objects.create(
                job_type='products',
                original_filename=file.name,
                file_size=file.size,
                created_by=request.user,
                status='processing',
                total_records=total_rows
            )
            
            for index, row in df.iterrows():
                row_num = index + 2  # Excel row number (1-indexed with header)
                
                try:
                    # Skip empty rows
                    if pd.isna(row.get('name')) or str(row.get('name')).strip() == '':
                        failed += 1
                        errors.append({
                            'row': row_num,
                            'error': 'Product name is required'
                        })
                        continue
                    
                    name = str(row['name']).strip()
                    
                    # Get or create category
                    category = None
                    if 'category' in df.columns and pd.notna(row.get('category')):
                        cat_name = str(row['category']).strip()
                        if cat_name:
                            category, _ = Category.objects.get_or_create(
                                name=cat_name,
                                defaults={'slug': cat_name.lower().replace(' ', '-')}
                            )
                    
                    # Get or create supplier
                    supplier = None
                    if 'supplier' in df.columns and pd.notna(row.get('supplier')):
                        sup_name = str(row['supplier']).strip()
                        if sup_name:
                            supplier, _ = Supplier.objects.get_or_create(
                                name=sup_name,
                                defaults={
                                    'phone': '',
                                    'email': f"{sup_name.lower().replace(' ', '')}@temp.com",
                                    'address_line1': 'To be updated'
                                }
                            )
                    
                    # Parse and validate prices
                    try:
                        cost_price = Decimal(str(row['cost_price']).replace(',', ''))
                        retail_price = Decimal(str(row['retail_price']).replace(',', ''))
                    except:
                        failed += 1
                        errors.append({
                            'row': row_num,
                            'error': f'Invalid price format: cost={row.get("cost_price")}, retail={row.get("retail_price")}'
                        })
                        continue
                    
                    if retail_price <= 0:
                        failed += 1
                        errors.append({
                            'row': row_num,
                            'error': f'Retail price must be greater than zero: {retail_price}'
                        })
                        continue
                    
                    if cost_price >= retail_price:
                        failed += 1
                        errors.append({
                            'row': row_num,
                            'error': f'Cost price ({cost_price}) must be less than retail price ({retail_price})'
                        })
                        continue
                    
                    # Wholesale price (optional)
                    wholesale_price = None
                    if 'wholesale_price' in df.columns and pd.notna(row.get('wholesale_price')):
                        try:
                            wp = Decimal(str(row['wholesale_price']).replace(',', ''))
                            if wp > 0 and wp < retail_price:
                                wholesale_price = wp
                        except:
                            pass
                    
                    # Stock quantity
                    try:
                        stock_quantity = Decimal(str(row['stock_quantity']).replace(',', ''))
                        if stock_quantity < 0:
                            stock_quantity = 0
                    except:
                        stock_quantity = 0
                    
                    # Reorder level
                    reorder_level = 0
                    if 'reorder_level' in df.columns and pd.notna(row.get('reorder_level')):
                        try:
                            reorder_level = Decimal(str(row['reorder_level']).replace(',', ''))
                        except:
                            pass
                    
                    # Unit validation
                    valid_units = ['piece', 'kg', 'g', 'l', 'ml', 'box', 'carton', 'pack']
                    unit = str(row.get('unit', 'piece')).lower().strip()
                    if unit not in valid_units:
                        unit = 'piece'
                    
                    # Tax rate validation
                    try:
                        tax_rate = int(row['tax_rate'])
                        if tax_rate not in [0, 8, 16]:
                            tax_rate = 16
                    except:
                        tax_rate = 16
                    
                    # SKU handling (optional)
                    sku = None
                    if 'sku' in df.columns and pd.notna(row.get('sku')):
                        sku = str(row['sku']).strip()
                    
                    # Barcode
                    barcode = ''
                    if 'barcode' in df.columns and pd.notna(row.get('barcode')):
                        barcode = str(row['barcode']).strip()
                    
                    # Description
                    description = ''
                    if 'description' in df.columns and pd.notna(row.get('description')):
                        description = str(row['description']).strip()
                    
                    # Create or update product
                    product, created = Product.objects.update_or_create(
                        sku=sku if sku else None,
                        defaults={
                            'name': name,
                            'barcode': barcode,
                            'category': category,
                            'supplier': supplier,
                            'cost_price': cost_price,
                            'retail_price': retail_price,
                            'wholesale_price': wholesale_price,
                            'stock_quantity': stock_quantity,
                            'reorder_level': reorder_level,
                            'unit': unit,
                            'tax_rate': tax_rate,
                            'description': description,
                            'is_active': True,
                        }
                    )
                    
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append({
                        'row': row_num,
                        'error': str(e)
                    })
            
            # Update import job
            import_job.successful_records = successful
            import_job.failed_records = failed
            import_job.error_log = errors[:100]  # Store first 100 errors
            import_job.status = 'completed' if failed == 0 else 'partial' if successful > 0 else 'failed'
            import_job.completed_at = timezone.now()
            import_job.save()
            
            return Response({
                'message': 'Import completed',
                'job_id': import_job.job_id,
                'total_rows': total_rows,
                'successful': successful,
                'failed': failed,
                'errors': errors[:20],  # Return first 20 errors
                'has_more_errors': len(errors) > 20
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to process file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], url_path='export')
    def export_products(self, request):
        """
        GET /api/products/export/
        
        Export products to Excel with formatting
        Optional query params: format=xlsx|csv, category=id, supplier=id
        """
        # Get filtered queryset
        queryset = self.get_queryset().filter(is_active=True)
        
        # Apply additional filters
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        supplier_id = request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        # Prepare data
        data = []
        for product in queryset:
            data.append({
                'SKU': product.sku,
                'Barcode': product.barcode,
                'Product Name': product.name,
                'Category': product.category.name if product.category else '',
                'Supplier': product.supplier.name if product.supplier else '',
                'Cost Price (KES)': float(product.cost_price),
                'Retail Price (KES)': float(product.retail_price),
                'Wholesale Price (KES)': float(product.wholesale_price) if product.wholesale_price else '',
                'Stock Quantity': float(product.stock_quantity),
                'Reorder Level': float(product.reorder_level),
                'Unit': product.unit,
                'Tax Rate (%)': product.tax_rate,
                'Profit Margin (%)': round(float(product.profit_margin), 2),
                'Stock Value (KES)': round(float(product.stock_value), 2),
                'Status': 'Active' if product.is_active else 'Inactive',
                'Last Updated': product.updated_at.strftime('%Y-%m-%d %H:%M:%S') if product.updated_at else '',
            })
        
        df = pd.DataFrame(data)
        
        # Check export format
        export_format = request.query_params.get('format', 'xlsx')
        
        if export_format == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            response = HttpResponse(
                output.getvalue(),
                content_type='text/csv'
            )
            response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
        else:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Products', index=False)
                
                # Add summary sheet
                summary_data = {
                    'Metric': ['Total Products', 'Total Stock Value', 'Average Price', 'Low Stock Items'],
                    'Value': [
                        len(data),
                        f"KES {sum(p.get('Stock Value (KES)', 0) for p in data):,.2f}",
                        f"KES {sum(p.get('Retail Price (KES)', 0) for p in data) / len(data) if data else 0:,.2f}",
                        sum(1 for p in data if p.get('Stock Quantity', 0) <= p.get('Reorder Level', 0))
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            output.seek(0)
            
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="products_export.xlsx"'
        
        return response
    
    @action(detail=False, methods=['get'], url_path='download-template')
    def download_template(self, request):
        """
        GET /api/products/download-template/
        
        Download Excel template for product import with instructions
        """
        output = io.BytesIO()
        
        # Create template DataFrame
        template_data = {
            'name': ['Example Product 1', 'Example Product 2', ''],
            'sku': ['', '', ''],
            'barcode': ['123456789012', '987654321098', ''],
            'category': ['Electronics', 'Clothing', ''],
            'supplier': ['Tech Distributors', 'Fashion Hub', ''],
            'cost_price': [100.00, 50.00, ''],
            'retail_price': [250.00, 120.00, ''],
            'wholesale_price': [200.00, 90.00, ''],
            'stock_quantity': [100, 200, ''],
            'reorder_level': [10, 20, ''],
            'unit': ['piece', 'piece', 'piece'],
            'tax_rate': [16, 16, 16],
            'description': ['High quality electronic product', 'Comfortable cotton shirt', ''],
            'is_active': ['Yes', 'Yes', 'Yes'],
        }
        
        df = pd.DataFrame(template_data)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Products', index=False)
            
            # Instructions sheet
            instructions_data = {
                'Column': ['name', 'sku', 'barcode', 'category', 'supplier', 
                          'cost_price', 'retail_price', 'wholesale_price', 
                          'stock_quantity', 'reorder_level', 'unit', 'tax_rate', 'description', 'is_active'],
                'Required': ['Yes', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'No', 'Yes', 'No', 'Yes', 'Yes', 'No', 'No'],
                'Data Type': ['Text', 'Text', 'Number', 'Text', 'Text', 'Number', 'Number', 'Number', 'Number', 'Number', 'Text', 'Number', 'Text', 'Yes/No'],
                'Description': [
                    'Product name (unique identifier for display)',
                    'Leave empty to auto-generate (format: CAT-XXXXXX)',
                    'Product barcode (must be unique if provided)',
                    'Category name (will be created automatically if new)',
                    'Supplier name (will be created automatically if new)',
                    'Purchase cost from supplier (KES)',
                    'Selling price to retail customers (KES)',
                    'Selling price to wholesale customers (KES) - optional',
                    'Current stock on hand',
                    'Alert when stock falls below this level',
                    'Unit: piece, kg, g, l, ml, box, carton, pack',
                    'Tax rate: 0, 8, or 16 percent',
                    'Product description (optional)',
                    'Yes or No (defaults to Yes)'
                ]
            }
            instructions_df = pd.DataFrame(instructions_data)
            instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
        
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="product_import_template.xlsx"'
        
        return response
    
    @action(detail=False, methods=['post'], url_path='bulk-price-update')
    def bulk_price_update(self, request):
        """
        POST /api/products/bulk-price-update/
        
        Bulk update product prices by percentage or fixed amount
        Body: {
            "update_type": "percentage",  # or "fixed"
            "adjustment": 10,  # 10% increase or +10 KES
            "price_field": "retail_price",  # retail_price, wholesale_price, cost_price
            "category_id": 1,  # optional
            "supplier_id": 1,  # optional
            "product_ids": [1,2,3]  # optional
        }
        """
        serializer = BulkPriceUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        update_type = data['update_type']
        adjustment = data['adjustment']
        price_field = data['price_field']
        
        # Get products to update
        queryset = Product.objects.filter(is_active=True)
        
        if data.get('product_ids'):
            queryset = queryset.filter(id__in=data['product_ids'])
        elif data.get('category_id'):
            queryset = queryset.filter(category_id=data['category_id'])
        elif data.get('supplier_id'):
            queryset = queryset.filter(supplier_id=data['supplier_id'])
        
        original_count = queryset.count()
        updated_count = 0
        updated_products = []
        
        for product in queryset:
            current_price = getattr(product, price_field)
            
            if current_price is None:
                continue
            
            if update_type == 'percentage':
                new_price = current_price * (Decimal(str(1 + adjustment / 100)))
            else:  # fixed
                new_price = current_price + Decimal(str(adjustment))
            
            # Ensure price doesn't go below zero
            new_price = max(Decimal('0'), new_price)
            
            # For wholesale/carton, ensure they don't exceed retail
            if price_field == 'wholesale_price' and product.retail_price and new_price >= product.retail_price:
                new_price = product.retail_price - Decimal('0.01')
            
            setattr(product, price_field, new_price)
            product.save(update_fields=[price_field, 'updated_at'])
            updated_count += 1
            
            updated_products.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'old_price': float(current_price),
                'new_price': float(new_price)
            })
        
        return Response({
            'message': f'Updated {updated_count} of {original_count} products',
            'updated_count': updated_count,
            'price_field': price_field,
            'update_type': update_type,
            'adjustment': adjustment,
            'updated_products': updated_products[:50]  # Return first 50 for preview
        })
    
    @action(detail=False, methods=['post'], url_path='bulk-update-stock')
    def bulk_update_stock(self, request):
        """
        POST /api/products/bulk-update-stock/
        
        Update stock for multiple products at once
        Body: {
            "updates": [
                {"sku": "ELEC-000001", "quantity": 100, "operation": "set"},
                {"barcode": "123456789", "quantity": 50, "operation": "add"},
                {"id": 1, "quantity": 20, "operation": "subtract"}
            ]
        }
        operation: set (absolute), add (increase), subtract (decrease)
        """
        updates = request.data.get('updates', [])
        
        if not updates:
            return Response(
                {"error": "No updates provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = {
            'successful': [],
            'failed': [],
            'total': len(updates)
        }
        
        for update in updates:
            operation = update.get('operation', 'set')
            quantity = Decimal(str(update.get('quantity', 0)))
            
            if quantity <= 0:
                results['failed'].append({
                    'identifier': update,
                    'error': 'Quantity must be greater than zero'
                })
                continue
            
            # Find product by different identifiers
            product = None
            identifier = None
            
            if 'id' in update:
                try:
                    product = Product.objects.get(id=update['id'], is_active=True)
                    identifier = f"ID:{update['id']}"
                except Product.DoesNotExist:
                    pass
            
            if not product and 'sku' in update:
                try:
                    product = Product.objects.get(sku=update['sku'], is_active=True)
                    identifier = f"SKU:{update['sku']}"
                except Product.DoesNotExist:
                    pass
            
            if not product and 'barcode' in update:
                try:
                    product = Product.objects.get(barcode=update['barcode'], is_active=True)
                    identifier = f"Barcode:{update['barcode']}"
                except Product.DoesNotExist:
                    pass
            
            if not product:
                results['failed'].append({
                    'identifier': update,
                    'error': 'Product not found'
                })
                continue
            
            old_stock = product.stock_quantity
            
            # Apply operation
            if operation == 'set':
                new_stock = quantity
            elif operation == 'add':
                new_stock = old_stock + quantity
            elif operation == 'subtract':
                if old_stock < quantity:
                    results['failed'].append({
                        'identifier': identifier,
                        'error': f'Insufficient stock. Available: {old_stock}, Requested reduction: {quantity}'
                    })
                    continue
                new_stock = old_stock - quantity
            else:
                results['failed'].append({
                    'identifier': identifier,
                    'error': f'Invalid operation: {operation}'
                })
                continue
            
            # Update stock
            product.stock_quantity = new_stock
            product.save(update_fields=['stock_quantity', 'updated_at'])
            
            # Record stock movement if we have inventory module
            try:
                from inventory.models import StockMovement
                StockMovement.objects.create(
                    product=product,
                    movement_type='adjustment',
                    quantity=abs(quantity),
                    stock_before=old_stock,
                    stock_after=new_stock,
                    unit_cost=product.cost_price,
                    reference_id='bulk_update',
                    recorded_by=request.user,
                    notes=f"Bulk stock update: {operation} {quantity} units"
                )
            except ImportError:
                pass  # Inventory module not installed
            
            results['successful'].append({
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'operation': operation,
                'old_stock': float(old_stock),
                'new_stock': float(new_stock),
                'change': float(quantity if operation in ['add', 'set'] else -quantity)
            })
        
        return Response({
            'message': f"Updated {len(results['successful'])} of {results['total']} products",
            'successful_count': len(results['successful']),
            'failed_count': len(results['failed']),
            'successful': results['successful'],
            'failed': results['failed'][:20]  # First 20 failures
        })
    
    @action(detail=False, methods=['post'], url_path='bulk-deactivate')
    def bulk_deactivate(self, request):
        """
        POST /api/products/bulk-deactivate/
        
        Deactivate multiple products at once
        Body: {"product_ids": [1,2,3]} or {"skus": ["SKU1", "SKU2"]}
        """
        product_ids = request.data.get('product_ids', [])
        skus = request.data.get('skus', [])
        
        if not product_ids and not skus:
            return Response(
                {"error": "Provide either product_ids or skus"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Product.objects.filter(is_active=True)
        
        if product_ids:
            queryset = queryset.filter(id__in=product_ids)
        if skus:
            queryset = queryset.filter(sku__in=skus)
        
        count = queryset.count()
        queryset.update(is_active=False)
        
        return Response({
            'message': f'Deactivated {count} products',
            'deactivated_count': count
        })
    
    @action(detail=True, methods=['post'], url_path='update-stock')
    def update_stock(self, request, pk=None):
        """
        POST /api/products/{id}/update-stock/
        
        Manually adjust stock quantity for a single product
        Body: {"quantity": 50, "operation": "add", "reason": "Restock from supplier"}
        operation: set, add, subtract
        """
        product = self.get_object()
        
        quantity = Decimal(str(request.data.get('quantity', 0)))
        operation = request.data.get('operation', 'add')
        reason = request.data.get('reason', '')
        
        if quantity <= 0:
            return Response(
                {"error": "Quantity must be greater than zero"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_stock = product.stock_quantity
        
        if operation == 'set':
            new_stock = quantity
        elif operation == 'add':
            new_stock = old_stock + quantity
        elif operation == 'subtract':
            if old_stock < quantity:
                return Response(
                    {"error": f"Insufficient stock. Available: {old_stock}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            new_stock = old_stock - quantity
        else:
            return Response(
                {"error": f"Invalid operation: {operation}. Use set, add, or subtract"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.stock_quantity = new_stock
        product.save(update_fields=['stock_quantity', 'updated_at'])
        
        # Record stock movement
        try:
            from inventory.models import StockMovement
            StockMovement.objects.create(
                product=product,
                movement_type='adjustment',
                quantity=abs(quantity),
                stock_before=old_stock,
                stock_after=new_stock,
                unit_cost=product.cost_price,
                recorded_by=request.user,
                notes=reason or f"Manual adjustment: {operation} {quantity} units"
            )
        except ImportError:
            pass
        
        return Response({
            'message': 'Stock updated successfully',
            'product_id': product.id,
            'product_name': product.name,
            'sku': product.sku,
            'operation': operation,
            'old_stock': float(old_stock),
            'new_stock': float(new_stock),
            'change': float(quantity if operation in ['add', 'set'] else -quantity)
        })
    
    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """
        GET /api/products/dashboard-stats/
        
        Get product statistics for dashboard
        """
        total_products = Product.objects.filter(is_active=True).count()
        low_stock_count = Product.objects.filter(
            is_active=True,
            stock_quantity__lte=F('reorder_level')
        ).exclude(reorder_level=0).count()
        
        out_of_stock = Product.objects.filter(is_active=True, stock_quantity=0).count()
        
        total_stock_value = Product.objects.aggregate(
            total=Sum(F('stock_quantity') * F('cost_price'))
        )['total'] or Decimal('0')
        
        total_retail_value = Product.objects.aggregate(
            total=Sum(F('stock_quantity') * F('retail_price'))
        )['total'] or Decimal('0')
        
        # Top categories by product count
        top_categories = Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0).order_by('-product_count')[:5]
        
        categories_data = [
            {'id': cat.id, 'name': cat.name, 'count': cat.product_count}
            for cat in top_categories
        ]
        
        # Top suppliers
        top_suppliers = Supplier.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0).order_by('-product_count')[:5]
        
        suppliers_data = [
            {'id': sup.id, 'name': sup.name, 'product_count': sup.product_count}
            for sup in top_suppliers
        ]
        
        return Response({
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock': out_of_stock,
            'total_stock_value': float(total_stock_value),
            'total_retail_value': float(total_retail_value),
            'potential_profit': float(total_retail_value - total_stock_value),
            'top_categories': categories_data,
            'top_suppliers': suppliers_data
        })
    
    @action(detail=False, methods=['get'], url_path='search')
    def advanced_search(self, request):
        """
        GET /api/products/search/?q=phone&min_price=1000&max_price=5000&category=1&in_stock=true
        
        Advanced product search with multiple filters
        """
        queryset = Product.objects.filter(is_active=True)
        
        # Search term
        q = request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(sku__icontains=q) |
                Q(barcode__icontains=q) |
                Q(description__icontains=q)
            )
        
        # Price filters
        min_price = request.query_params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(retail_price__gte=Decimal(min_price))
            except:
                pass
        
        max_price = request.query_params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(retail_price__lte=Decimal(max_price))
            except:
                pass
        
        # Category filter
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Supplier filter
        supplier_id = request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        # Stock filter
        in_stock = request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)
        
        low_stock = request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__lte=F('reorder_level')).exclude(reorder_level=0)
        
        # Sorting
        sort_by = request.query_params.get('sort_by', 'name')
        sort_order = request.query_params.get('sort_order', 'asc')
        
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        
        if sort_by in ['name', 'retail_price', 'stock_quantity', 'created_at']:
            queryset = queryset.order_by(sort_by)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product Images
    """
    
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter images by product if product_id provided"""
        product_id = self.request.query_params.get('product_id')
        if product_id:
            return ProductImage.objects.filter(product_id=product_id)
        return ProductImage.objects.all()
    
    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, pk=None):
        """Set this image as the primary image for the product"""
        image = self.get_object()
        
        # Remove primary flag from other images of same product
        ProductImage.objects.filter(product=image.product).update(is_primary=False)
        
        # Set this image as primary
        image.is_primary = True
        image.save()
        
        return Response({'message': 'Primary image set successfully'})


=======
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_create(self, serializer):
        product = serializer.save()
        send_notification(request.user, f"📦 New product added: {product.name}")

    def perform_update(self, serializer):
        product = serializer.save()

        send_notification(request.user, f"✏️ Product updated: {product.name}")

        if product.stock < 20:
            send_notification(request.user, f"⚠️ Low stock alert: {product.name}: Only {product.stock} left!")
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
