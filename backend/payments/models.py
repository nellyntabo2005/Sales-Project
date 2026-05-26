# payments/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
from datetime import datetime, timezone

from customers.models import Customer
from users.models import User
from sales.models import Sale


class PaymentAccount(models.Model):
    """
    Payment accounts (Cash, M-Pesa, Bank, Mobile Money, etc.)
    Tracks all financial accounts in the system
    """
    
    ACCOUNT_TYPES = [
        ('cash', 'Cash Register'),
        ('mpesa', 'M-Pesa Paybill/Till'),
        ('bank', 'Bank Account'),
        ('mobile_money', 'Other Mobile Money'),
        ('credit', 'Customer Credit Account'),
        ('petty_cash', 'Petty Cash'),
    ]
    
    name = models.CharField(max_length=100, help_text="Account name (e.g., Main Cash Register)")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_number = models.CharField(max_length=100, blank=True, help_text="Account number or reference")
    
    # For cash registers
    cashier_responsible = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cash_registers'
    )
    
    # For M-Pesa
    mpesa_shortcode = models.CharField(max_length=20, blank=True, help_text="Paybill or Till number")
    mpesa_paybill = models.CharField(max_length=20, blank=True)
    mpesa_till = models.CharField(max_length=20, blank=True)
    
    # For bank
    bank_name = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    bank_account_name = models.CharField(max_length=200, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_sort_code = models.CharField(max_length=20, blank=True)
    bank_swift_code = models.CharField(max_length=20, blank=True)
    
    # Opening and current balances
    opening_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Balance at start of financial period"
    )
    current_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Current available balance"
    )
    
    # Limits
    minimum_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Alert when balance falls below this"
    )
    maximum_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum allowed balance"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default account for this type")
    
    # Additional info
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['account_type', 'name']
        indexes = [
            models.Index(fields=['account_type', 'is_active']),
            models.Index(fields=['name']),
            models.Index(fields=['mpesa_shortcode']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()}) - Balance: {self.current_balance}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default account per type
        if self.is_default:
            PaymentAccount.objects.filter(
                account_type=self.account_type, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        # Check minimum balance alert
        if self.current_balance < self.minimum_balance:
            # This will trigger notification system
            pass
        
        super().save(*args, **kwargs)
    
    def update_balance(self, amount, operation='add'):
        """Update account balance safely"""
        if operation == 'add':
            self.current_balance += amount
        elif operation == 'subtract':
            if self.current_balance < amount:
                raise ValidationError(f"Insufficient balance in {self.name}")
            self.current_balance -= amount
        else:
            self.current_balance = amount
        
        self.save(update_fields=['current_balance', 'updated_at'])
        return self.current_balance


class PaymentTransaction(models.Model):
    """
    All financial transactions (payments, receipts, refunds, expenses)
    Central ledger for all money movement
    """
    
    TRANSACTION_TYPES = [
        ('sale', 'Sale Payment'),
        ('refund', 'Refund to Customer'),
        ('supplier_payment', 'Supplier Payment'),
        ('expense', 'Expense'),
        ('salary', 'Salary Payment'),
        ('transfer', 'Account Transfer'),
        ('deposit', 'Cash Deposit'),
        ('withdrawal', 'Cash Withdrawal'),
        ('purchase', 'Purchase Payment'),
        ('return_refund', 'Supplier Return Refund'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('credit', 'Store Credit'),
        ('loyalty', 'Loyalty Points'),
        ('mixed', 'Mixed Payment'),
    ]
<<<<<<< HEAD
    
    STATUS_CHOICES = [
=======

    PAYMENT_STATUS = [
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
<<<<<<< HEAD
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    ]
    
    # Identifiers
    transaction_id = models.CharField(
        max_length=50, 
        unique=True, 
        editable=False,
        help_text="Unique transaction reference number"
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, db_index=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, db_index=True)
    
    # Amounts
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    fee = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Transaction fee (e.g., M-Pesa charges)"
    )
    tax = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Tax on transaction"
    )
    net_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        editable=False,
        help_text="Amount - fee - tax"
    )
    
    # Accounts
    from_account = models.ForeignKey(
        PaymentAccount, 
        on_delete=models.PROTECT, 
        related_name='outgoing_transactions',
        null=True,
        blank=True,
        help_text="Source account (money coming FROM)"
    )
    to_account = models.ForeignKey(
        PaymentAccount, 
        on_delete=models.PROTECT, 
        related_name='incoming_transactions',
        null=True,
        blank=True,
        help_text="Destination account (money going TO)"
    )
    
    # References
    reference_number = models.CharField(
        max_length=100, 
        blank=True, 
        db_index=True,
        help_text="External reference (cheque number, M-Pesa code, etc.)"
    )
=======
    ]

>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='payment_transactions'
    )
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='payments'
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Description
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Audit
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='payment_transactions'
    )
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_payments'
    )
<<<<<<< HEAD
    
    # Timestamps
    transaction_date = models.DateTimeField(auto_now_add=True, db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['sale']),
            models.Index(fields=['customer']),
            models.Index(fields=['transaction_date']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Auto-generate transaction ID
        if not self.transaction_id:
            date_str = datetime.now().strftime('%Y%m%d')
            last_txn = PaymentTransaction.objects.filter(
                transaction_id__startswith=f'TXN-{date_str}'
            ).order_by('-transaction_id').first()
            
            if last_txn:
                try:
                    last_num = int(last_txn.transaction_id.split('-')[-1])
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1
            else:
                new_num = 1
            
            self.transaction_id = f"TXN-{date_str}-{new_num:06d}"
        
        # Calculate net amount
        self.net_amount = self.amount - self.fee - self.tax
        
        # Update account balances if completed
        if self.pk:  # Existing transaction
            old = PaymentTransaction.objects.get(pk=self.pk)
            if old.status != 'completed' and self.status == 'completed':
                self._update_account_balances()
            elif old.status == 'completed' and self.status != 'completed':
                self._reverse_account_balances()
        
        super().save(*args, **kwargs)
    
    def _update_account_balances(self):
        """Update account balances when transaction is completed"""
        if self.transaction_type == 'sale' and self.to_account:
            self.to_account.update_balance(self.net_amount, 'add')
        elif self.transaction_type == 'refund' and self.from_account:
            self.from_account.update_balance(self.amount, 'subtract')
        elif self.transaction_type == 'expense' and self.from_account:
            self.from_account.update_balance(self.amount, 'subtract')
        elif self.transaction_type == 'deposit' and self.to_account:
            self.to_account.update_balance(self.amount, 'add')
        elif self.transaction_type == 'withdrawal' and self.from_account:
            self.from_account.update_balance(self.amount, 'subtract')
        elif self.transaction_type == 'transfer':
            if self.from_account:
                self.from_account.update_balance(self.amount, 'subtract')
            if self.to_account:
                self.to_account.update_balance(self.amount, 'add')
    
    def _reverse_account_balances(self):
        """Reverse account balance updates when transaction is un-completed"""
        if self.transaction_type == 'sale' and self.to_account:
            self.to_account.update_balance(self.net_amount, 'subtract')
        elif self.transaction_type == 'refund' and self.from_account:
            self.from_account.update_balance(self.amount, 'add')
        # ... similar for other types
    
    def verify(self, verified_by_user):
        """Mark transaction as verified"""
        self.status = 'completed'
        self.verified_by = verified_by_user
        self.verified_at = datetime.now()
        self.save()
        return True
    
    def cancel(self):
        """Cancel a pending transaction"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.save()
            return True
        return False


# ============================================================
# M-PESA INTEGRATION MODELS
# ============================================================

class MpesaAccount(models.Model):
    """
    M-Pesa Paybill/Till Account Configuration
    Supports multiple accounts for different branches
    """
    
    BUSINESS_TYPES = [
        ('paybill', 'Paybill'),
        ('till', 'Till Number'),
    ]
    
    ENVIRONMENT_CHOICES = [
        ('sandbox', 'Sandbox (Testing)'),
        ('production', 'Production (Live)'),
    ]
    
    name = models.CharField(max_length=100, help_text="Account name (e.g., Main Store Paybill)")
    business_type = models.CharField(max_length=10, choices=BUSINESS_TYPES)
    
    # Paybill/Till details
    shortcode = models.CharField(max_length=10, help_text="Paybill or Till number")
    passkey = models.CharField(max_length=100, help_text="API Passkey from Daraja portal")
    consumer_key = models.CharField(max_length=100)
    consumer_secret = models.CharField(max_length=100)
    
    # Environment
    environment = models.CharField(max_length=20, choices=ENVIRONMENT_CHOICES, default='sandbox')
    
    # Callback URLs
    callback_url = models.URLField(help_text="URL for transaction callbacks")
    timeout_url = models.URLField(help_text="URL for timeout callbacks")
    result_url = models.URLField(help_text="URL for result callbacks (for B2C)")
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Business details
    business_name = models.CharField(max_length=200, blank=True)
    business_shortcode = models.CharField(max_length=20, blank=True, help_text="Shortcode for receipts")
    
    # Link to payment account
    payment_account = models.OneToOneField(
        PaymentAccount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mpesa_config',
        help_text="Linked payment account for reconciliation"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', 'name']
        indexes = [
            models.Index(fields=['shortcode']),
            models.Index(fields=['environment']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.shortcode}) - {self.environment}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            MpesaAccount.objects.filter(is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def api_base_url(self):
        """Get M-Pesa API base URL based on environment"""
        if self.environment == 'sandbox':
            return 'https://sandbox.safaricom.co.ke'
        return 'https://api.safaricom.co.ke'


class MpesaTransaction(models.Model):
    """
    M-Pesa transaction record
    Links to PaymentTransaction for reconciliation
    """
    
    TRANSACTION_TYPES = [
        ('c2b', 'Customer to Business (Payment)'),
        ('b2c', 'Business to Customer (Refund/Withdrawal)'),
        ('stk_push', 'STK Push (Lipa Na M-Pesa)'),
        ('reversal', 'Transaction Reversal'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('timeout', 'Timeout'),
    ]
    
    # M-Pesa reference
    merchant_request_id = models.CharField(max_length=100, unique=True, null=True, blank=True, db_index=True)
    checkout_request_id = models.CharField(max_length=100, unique=True, null=True, blank=True, db_index=True)
    mpesa_receipt_number = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Customer details
    phone_number = models.CharField(max_length=15, db_index=True, help_text="Customer M-Pesa phone number")
    account_reference = models.CharField(max_length=50, help_text="Account reference (e.g., Invoice number)")
    transaction_desc = models.CharField(max_length=100, blank=True)
    
    # M-Pesa response data
    response_code = models.CharField(max_length=10, blank=True)
    response_description = models.CharField(max_length=200, blank=True)
    
    # Callback data (JSON)
    callback_data = models.JSONField(default=dict, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.CharField(max_length=500, blank=True)
    
    # Links to other modules
    payment_transaction = models.ForeignKey(
        PaymentTransaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mpesa_transactions'
    )
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mpesa_transactions'
    )
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mpesa_transactions'
    )
    
    # Which account processed this
    mpesa_account = models.ForeignKey(
        MpesaAccount, 
        on_delete=models.PROTECT, 
        related_name='transactions'
    )
    
    # For debugging
    raw_request = models.JSONField(default=dict, blank=True, help_text="Raw request sent to M-Pesa")
    raw_response = models.JSONField(default=dict, blank=True, help_text="Raw response from M-Pesa")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant_request_id']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['mpesa_receipt_number']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.mpesa_receipt_number or self.checkout_request_id} - {self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Auto-create account reference if not provided
        if not self.account_reference and self.sale:
            self.account_reference = self.sale.sale_id
        
        super().save(*args, **kwargs)
    
    def mark_completed(self, receipt_number, result_code=0, result_desc='Success'):
        """Mark transaction as completed"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.mpesa_receipt_number = receipt_number
        self.result_code = result_code
        self.result_desc = result_desc
        self.completed_at = timezone.now()
        self.save()
        
        # Create PaymentTransaction if not already linked
        if not self.payment_transaction:
            payment_txn = PaymentTransaction.objects.create(
                transaction_type='sale',
                payment_method='mpesa',
                amount=self.amount,
                reference_number=self.mpesa_receipt_number,
                sale=self.sale,
                customer=self.customer or (self.sale.customer if self.sale else None),
                description=f"M-Pesa payment for {self.account_reference}",
                recorded_by=None,  # System recorded
                status='completed',
                to_account=self.mpesa_account.payment_account if self.mpesa_account.payment_account else None
            )
            
            self.payment_transaction = payment_txn
            self.save()
            
            # Update sale payment status if linked
            if self.sale:
                self.sale.amount_paid += self.amount
                self.sale.save()
        
        return True
    
    def mark_failed(self, result_code, result_desc):
        """Mark transaction as failed"""
        self.status = 'failed'
        self.result_code = result_code
        self.result_desc = result_desc
        self.save()
        return False
    
    @property
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == 'completed' and self.result_code == 0


class MpesaCallbackLog(models.Model):
    """
    Store raw M-Pesa callbacks for debugging and audit
    """
    transaction = models.ForeignKey(
        MpesaTransaction, 
        on_delete=models.CASCADE, 
        related_name='callback_logs',
        null=True,
        blank=True
    )
    
    # Raw data
    raw_data = models.JSONField()
    
    # Processed
    result_code = models.IntegerField()
    result_desc = models.CharField(max_length=500)
    
    # IP address of caller
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Headers (for debugging)
    headers = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['result_code']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Callback for {self.transaction} at {self.created_at}"


class MpesaReconciliation(models.Model):
    """
    Daily M-Pesa reconciliation reports
    Match M-Pesa transactions with system payments
    """
    
    reconciliation_date = models.DateField(unique=True, db_index=True)
    mpesa_account = models.ForeignKey(MpesaAccount, on_delete=models.PROTECT, related_name='reconciliations')
    
    # Totals from M-Pesa
    mpesa_total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mpesa_total_count = models.IntegerField(default=0)
    
    # Totals from system
    system_total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    system_total_count = models.IntegerField(default=0)
    
    # Discrepancies
    discrepancy_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discrepancy_count = models.IntegerField(default=0)
    
    # Unmatched transactions (JSON)
    unmatched_from_mpesa = models.JSONField(default=list)
    unmatched_from_system = models.JSONField(default=list)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('matched', 'All Matched'),
        ('discrepancy', 'Has Discrepancies'),
        ('resolved', 'Resolved'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Notes
    notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-reconciliation_date']
        indexes = [
            models.Index(fields=['reconciliation_date', 'status']),
        ]
    
    def __str__(self):
        return f"Reconciliation {self.reconciliation_date} - {self.status}"
    
    def calculate_discrepancy(self):
        """Calculate discrepancy between M-Pesa and system"""
        self.discrepancy_amount = self.mpesa_total_amount - self.system_total_amount
        self.discrepancy_count = self.mpesa_total_count - self.system_total_count
        
        if self.discrepancy_amount == 0 and self.discrepancy_count == 0:
            self.status = 'matched'
        else:
            self.status = 'discrepancy'
        
        self.save()


# ============================================================
# ADDITIONAL PAYMENT MODELS
# ============================================================

class PaymentReconciliation(models.Model):
    """
    General payment reconciliation (not M-Pesa specific)
    For matching bank statements with system payments
    """
    
    reconciliation_date = models.DateField(db_index=True)
    
    # Account being reconciled
    account = models.ForeignKey(PaymentAccount, on_delete=models.PROTECT, related_name='reconciliations')
    
    # Statement data
    statement_balance = models.DecimalField(max_digits=15, decimal_places=2)
    system_balance = models.DecimalField(max_digits=15, decimal_places=2)
    difference = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    # Unreconciled items
    unreconciled_transactions = models.JSONField(default=list)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reconciled', 'Reconciled'),
        ('partial', 'Partially Reconciled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Notes
    notes = models.TextField(blank=True)
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-reconciliation_date']
        unique_together = ['reconciliation_date', 'account']
    
    def __str__(self):
        return f"Reconciliation {self.reconciliation_date} - {self.account.name}"
    
    def save(self, *args, **kwargs):
        self.difference = self.statement_balance - self.system_balance
        super().save(*args, **kwargs)


class ExpenseCategory(models.Model):
    """
    Categories for expenses
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    Business expenses tracking
    """
    expense_number = models.CharField(max_length=50, unique=True, editable=False)
    
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    description = models.TextField()
    receipt_image = models.ImageField(upload_to='expenses/', null=True, blank=True)
    
    # Payment
    payment_transaction = models.OneToOneField(
        PaymentTransaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='expense'
    )
    
    # Approval
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='expenses_requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_approved')
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    expense_date = models.DateField(db_index=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date']
        indexes = [
            models.Index(fields=['expense_number']),
            models.Index(fields=['status']),
            models.Index(fields=['expense_date']),
        ]
    
    def __str__(self):
        return f"{self.expense_number} - {self.category.name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.expense_number:
            date_str = datetime.now().strftime('%Y%m%d')
            last_expense = Expense.objects.filter(
                expense_number__startswith=f'EXP-{date_str}'
            ).order_by('-expense_number').first()
            
            if last_expense:
                try:
                    last_num = int(last_expense.expense_number.split('-')[-1])
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1
            else:
                new_num = 1
            
            self.expense_number = f"EXP-{date_str}-{new_num:04d}"
        
        self.total_amount = self.amount + self.tax_amount
        super().save(*args, **kwargs)
=======

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )

    payment_date = models.DateTimeField(auto_now_add=True)
    
    # M-Pesa specific fields
    mpesa_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="M-Pesa transaction ID"
    )
    
    mpesa_checkout_request_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Checkout request ID from STK push"
    )
    
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Customer phone number for M-Pesa"
    )

    def __str__(self):
        return f"Payment for Sale {self.sale_id} - {self.get_payment_method_display()}"


    
>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
