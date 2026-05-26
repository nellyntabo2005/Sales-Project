# products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Supplier, Product, ProductImage  # Remove 'Batch' from here


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'level', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'email', 'city', 'is_active', 'is_preferred']
    list_filter = ['is_active', 'is_preferred', 'city']
    search_fields = ['name', 'code', 'phone', 'email']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'sku', 'name', 'category', 'retail_price', 'stock_quantity',
        'reorder_level', 'is_active'
    ]
    
    list_filter = ['category', 'supplier', 'is_active', 'unit', 'tax_rate']
    search_fields = ['sku', 'barcode', 'name', 'description']
    
    readonly_fields = ['sku', 'uuid', 'created_at', 'updated_at']
    
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Identification', {
            'fields': ('sku', 'barcode', 'uuid', 'name', 'description')
        }),
        ('Classification', {
            'fields': ('category', 'supplier', 'supplier_sku', 'unit')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'retail_price', 'wholesale_price', 'carton_price', 'carton_quantity')
        }),
        ('Stock Management', {
            'fields': ('stock_quantity', 'reorder_level', 'reorder_quantity', 'minimum_stock', 'maximum_stock')
        }),
        ('Tax & Shipping', {
            'fields': ('tax_rate', 'weight', 'length', 'width', 'height')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'is_digital', 'main_image')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_purchased_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'caption', 'is_primary', 'order']
    list_filter = ['is_primary']
    search_fields = ['product__name', 'caption']


# REMOVE the BatchAdmin registration since Batch is now in inventory app
# @admin.register(Batch)
# class BatchAdmin(admin.ModelAdmin):
#     list_display = ['batch_number', 'product', 'quantity', 'remaining_quantity', 'expiry_date']