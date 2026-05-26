# payments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PaymentAccount, 
    PaymentTransaction, 
    MpesaAccount, 
    MpesaTransaction, 
    MpesaCallbackLog,
    MpesaReconciliation,
    ExpenseCategory,
    Expense
)


@admin.register(PaymentAccount)
class PaymentAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'current_balance', 'is_active', 'is_default']
    list_filter = ['account_type', 'is_active', 'is_default']
    search_fields = ['name', 'account_number']
    readonly_fields = ['current_balance', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'account_type', 'account_number', 'description')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_branch', 'bank_account_name', 'bank_account_number'),
            'classes': ('collapse',)
        }),
        ('M-Pesa Details', {
            'fields': ('mpesa_shortcode', 'mpesa_paybill', 'mpesa_till'),
            'classes': ('collapse',)
        }),
        ('Balance', {
            'fields': ('opening_balance', 'current_balance', 'minimum_balance', 'maximum_balance')
        }),
        ('Status', {
            'fields': ('is_active', 'is_default', 'cashier_responsible')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'transaction_type', 'payment_method', 
        'amount', 'status', 'transaction_date'
    ]
    list_filter = ['transaction_type', 'payment_method', 'status', 'transaction_date']
    search_fields = ['transaction_id', 'reference_number', 'description']
    readonly_fields = ['transaction_id', 'uuid', 'net_amount', 'transaction_date', 'updated_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'transaction_type', 'payment_method', 'status')
        }),
        ('Amounts', {
            'fields': ('amount', 'fee', 'tax', 'net_amount')
        }),
        ('Accounts', {
            'fields': ('from_account', 'to_account')
        }),
        ('References', {
            'fields': ('reference_number', 'sale', 'customer')
        }),
        ('Description', {
            'fields': ('description', 'notes')
        }),
        ('Audit', {
            'fields': ('recorded_by', 'verified_by', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('transaction_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MpesaAccount)
class MpesaAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'shortcode', 'business_type', 'environment', 'is_active', 'is_default']
    list_filter = ['business_type', 'environment', 'is_active', 'is_default']
    search_fields = ['name', 'shortcode']
    readonly_fields = ['created_at', 'updated_at']
    
    # Hide sensitive fields
    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return ['passkey', 'consumer_key', 'consumer_secret']
        return []


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'mpesa_receipt_number', 'amount', 'phone_number', 
        'status', 'transaction_type', 'created_at'
    ]
    list_filter = ['status', 'transaction_type', 'created_at']
    search_fields = ['mpesa_receipt_number', 'checkout_request_id', 'phone_number']
    readonly_fields = ['merchant_request_id', 'checkout_request_id', 'created_at', 'completed_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('mpesa_receipt_number', 'transaction_type', 'amount', 'status')
        }),
        ('Customer', {
            'fields': ('phone_number', 'account_reference', 'transaction_desc')
        }),
        ('Response Data', {
            'fields': ('response_code', 'response_description', 'result_code', 'result_desc')
        }),
        ('Links', {
            'fields': ('payment_transaction', 'sale', 'customer', 'mpesa_account')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)} if hasattr(ExpenseCategory, 'slug') else {}


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_number', 'category', 'amount', 'status', 'expense_date']
    list_filter = ['status', 'category', 'expense_date']
    search_fields = ['expense_number', 'description']
    readonly_fields = ['expense_number', 'total_amount', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Expense Information', {
            'fields': ('expense_number', 'category', 'description', 'amount', 'tax_amount', 'total_amount')
        }),
        ('Payment', {
            'fields': ('payment_transaction', 'status')
        }),
        ('Approval', {
            'fields': ('requested_by', 'approved_by', 'approved_at')
        }),
        ('Documents', {
            'fields': ('receipt_image', 'notes')
        }),
        ('Timestamps', {
            'fields': ('expense_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MpesaCallbackLog)
class MpesaCallbackLogAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'result_code', 'result_desc', 'created_at']
    list_filter = ['result_code', 'created_at']
    readonly_fields = ['transaction', 'raw_data', 'result_code', 'result_desc', 'ip_address', 'created_at']
    search_fields = ['transaction__mpesa_receipt_number']


@admin.register(MpesaReconciliation)
class MpesaReconciliationAdmin(admin.ModelAdmin):
    list_display = ['reconciliation_date', 'mpesa_account', 'status', 'discrepancy_amount']
    list_filter = ['status', 'reconciliation_date']
    search_fields = ['reconciliation_date']
    readonly_fields = ['created_at', 'resolved_at']


