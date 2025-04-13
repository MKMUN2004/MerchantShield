from django.contrib import admin
from .models import (
    Merchant,
    TransactionPattern,
    VerificationFlag,
    VerificationReport,
    AuditLog
)

@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'status', 'risk_level', 'created_at')
    list_filter = ('status', 'business_type', 'risk_level', 'country')
    search_fields = ('name', 'registration_number', 'email', 'website')
    readonly_fields = ('created_at', 'updated_at', 'last_verified_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'business_type', 'registration_number', 'tax_id', 'website')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Verification Status', {
            'fields': ('status', 'risk_level', 'risk_score')
        }),
        ('Verification Data', {
            'fields': ('verification_data', 'external_api_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_verified_at')
        }),
        ('Users', {
            'fields': ('created_by', 'verified_by')
        }),
    )


@admin.register(TransactionPattern)
class TransactionPatternAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'average_transaction_amount', 'monthly_transaction_volume', 'chargeback_rate', 'analysis_date')
    list_filter = ('analysis_date',)
    search_fields = ('merchant__name',)


@admin.register(VerificationFlag)
class VerificationFlagAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'flag_type', 'severity', 'status', 'created_at')
    list_filter = ('flag_type', 'severity', 'status')
    search_fields = ('merchant__name', 'description')
    readonly_fields = ('created_at', 'resolved_at')
    fieldsets = (
        ('Flag Information', {
            'fields': ('merchant', 'flag_type', 'description', 'severity', 'status')
        }),
        ('Resolution', {
            'fields': ('resolution_notes', 'resolved_at', 'resolved_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by')
        }),
    )


@admin.register(VerificationReport)
class VerificationReportAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'report_date', 'generated_by')
    list_filter = ('report_date',)
    search_fields = ('merchant__name',)
    readonly_fields = ('report_date',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'action', 'user', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('merchant__name', 'user__username')
    readonly_fields = ('merchant', 'action', 'user', 'timestamp', 'ip_address', 'details')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
