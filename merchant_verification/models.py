from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Merchant(models.Model):
    """Model representing a merchant to be verified"""
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('flagged', 'Flagged for Review'),
        ('rejected', 'Rejected'),
    ]
    
    BUSINESS_TYPE_CHOICES = [
        ('retail', 'Retail'),
        ('online', 'Online/E-commerce'),
        ('service', 'Service Provider'),
        ('financial', 'Financial Services'),
        ('gambling', 'Gambling/Gaming'),
        ('travel', 'Travel/Hospitality'),
        ('healthcare', 'Healthcare'),
        ('other', 'Other'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('extreme', 'Extreme Risk'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPE_CHOICES)
    registration_number = models.CharField(max_length=100, unique=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Verification Status
    status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )
    risk_level = models.CharField(
        max_length=20, 
        choices=RISK_LEVEL_CHOICES,
        blank=True,
        null=True
    )
    risk_score = models.FloatField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_verified_at = models.DateTimeField(blank=True, null=True)
    
    # Verification data
    verification_data = models.JSONField(blank=True, null=True)
    external_api_response = models.JSONField(blank=True, null=True)
    
    # Foreign keys
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_merchants',
        null=True
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='verified_merchants',
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        if self.status == 'verified' and not self.last_verified_at:
            self.last_verified_at = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Merchant'
        verbose_name_plural = 'Merchants'


class TransactionPattern(models.Model):
    """Model for storing transaction patterns of a merchant"""
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='transaction_patterns'
    )
    average_transaction_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    monthly_transaction_volume = models.IntegerField(blank=True, null=True)
    high_risk_countries_percentage = models.FloatField(blank=True, null=True)
    unusual_hours_percentage = models.FloatField(blank=True, null=True)
    similar_transactions_percentage = models.FloatField(blank=True, null=True)
    chargeback_rate = models.FloatField(blank=True, null=True)
    transaction_data = models.JSONField(blank=True, null=True)
    analysis_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transaction Pattern for {self.merchant.name}"
    
    class Meta:
        ordering = ['-analysis_date']
        verbose_name = 'Transaction Pattern'
        verbose_name_plural = 'Transaction Patterns'


class VerificationFlag(models.Model):
    """Model for storing verification flags for merchants"""
    FLAG_TYPE_CHOICES = [
        ('suspicious_website', 'Suspicious Website Content'),
        ('missing_info', 'Missing Critical Information'),
        ('high_risk_location', 'High Risk Location'),
        ('transaction_pattern', 'Unusual Transaction Pattern'),
        ('external_data', 'External Data Discrepancy'),
        ('regulatory', 'Regulatory Concern'),
        ('other', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='verification_flags'
    )
    flag_type = models.CharField(max_length=50, choices=FLAG_TYPE_CHOICES)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_flags',
        null=True
    )
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='resolved_flags',
        null=True,
        blank=True
    )
    resolution_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_flag_type_display()} Flag for {self.merchant.name}"
    
    def resolve(self, user, notes):
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.save()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Verification Flag'
        verbose_name_plural = 'Verification Flags'


class VerificationReport(models.Model):
    """Model for storing verification reports"""
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='verification_reports'
    )
    report_date = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    report_data = models.JSONField()
    risk_assessment = models.TextField()
    recommendations = models.TextField()
    
    def __str__(self):
        return f"Verification Report for {self.merchant.name} ({self.report_date.date()})"
    
    class Meta:
        ordering = ['-report_date']
        verbose_name = 'Verification Report'
        verbose_name_plural = 'Verification Reports'


class AuditLog(models.Model):
    """Model for auditing all verification activities"""
    ACTION_CHOICES = [
        ('create', 'Create Merchant'),
        ('update', 'Update Merchant'),
        ('verify', 'Verify Merchant'),
        ('flag', 'Flag Merchant'),
        ('review', 'Review Merchant'),
        ('reject', 'Reject Merchant'),
        ('report', 'Generate Report'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.user} on {self.merchant.name}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
