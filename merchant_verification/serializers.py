from rest_framework import serializers
from .models import (
    Merchant, 
    TransactionPattern, 
    VerificationFlag, 
    VerificationReport
)


class TransactionPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionPattern
        fields = [
            'id', 'average_transaction_amount', 'monthly_transaction_volume',
            'high_risk_countries_percentage', 'unusual_hours_percentage',
            'similar_transactions_percentage', 'chargeback_rate',
            'analysis_date'
        ]


class VerificationFlagSerializer(serializers.ModelSerializer):
    flag_type_display = serializers.CharField(source='get_flag_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by = serializers.StringRelatedField()
    resolved_by = serializers.StringRelatedField()
    
    class Meta:
        model = VerificationFlag
        fields = [
            'id', 'flag_type', 'flag_type_display', 'description', 'severity', 
            'severity_display', 'status', 'status_display', 'created_at', 
            'created_by', 'resolved_at', 'resolved_by', 'resolution_notes'
        ]


class MerchantSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    created_by = serializers.StringRelatedField()
    verified_by = serializers.StringRelatedField()
    transaction_patterns = TransactionPatternSerializer(many=True, read_only=True)
    verification_flags = VerificationFlagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Merchant
        fields = [
            'id', 'name', 'business_type', 'business_type_display',
            'registration_number', 'tax_id', 'website', 'email', 'phone',
            'address', 'city', 'state', 'country', 'postal_code',
            'status', 'status_display', 'risk_level', 'risk_level_display',
            'risk_score', 'created_at', 'updated_at', 'last_verified_at',
            'created_by', 'verified_by', 'transaction_patterns', 'verification_flags'
        ]


class MerchantListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    flag_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Merchant
        fields = [
            'id', 'name', 'business_type', 'business_type_display',
            'registration_number', 'website', 'country',
            'status', 'status_display', 'risk_level', 'risk_level_display',
            'risk_score', 'created_at', 'flag_count'
        ]
    
    def get_flag_count(self, obj):
        return obj.verification_flags.filter(status__in=['open', 'investigating']).count()


class VerificationReportSerializer(serializers.ModelSerializer):
    merchant = MerchantListSerializer(read_only=True)
    generated_by = serializers.StringRelatedField()
    
    class Meta:
        model = VerificationReport
        fields = [
            'id', 'merchant', 'report_date', 'generated_by',
            'risk_assessment', 'recommendations', 'report_data'
        ]


class MerchantVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ['status', 'risk_level', 'risk_score', 'verification_data']
