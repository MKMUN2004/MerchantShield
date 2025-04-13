from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone

from ..models import (
    Merchant, 
    TransactionPattern, 
    VerificationFlag, 
    VerificationReport,
    AuditLog
)
from ..serializers import (
    MerchantSerializer,
    MerchantListSerializer,
    MerchantVerificationSerializer,
    TransactionPatternSerializer,
    VerificationFlagSerializer,
    VerificationReportSerializer
)
from ..ml_models.risk_assessment import assess_merchant_risk
from ..ml_models.transaction_analysis import analyze_transaction_patterns
from ..services.external_api import verify_merchant_external


class MerchantListView(generics.ListCreateAPIView):
    """API endpoint for listing and creating merchants"""
    serializer_class = MerchantListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Merchant.objects.all()
        
        # Filter by name
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        # Filter by business type
        business_type = self.request.query_params.get('business_type', None)
        if business_type:
            queryset = queryset.filter(business_type=business_type)
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by risk level
        risk_level = self.request.query_params.get('risk_level', None)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        # Filter by country
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        merchant = serializer.save(
            created_by=self.request.user,
            status='pending'
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=self.request.user,
            merchant=merchant,
            action='create'
        )


class MerchantDetailView(generics.RetrieveUpdateAPIView):
    """API endpoint for retrieving and updating a merchant"""
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        merchant = serializer.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=self.request.user,
            merchant=merchant,
            action='update'
        )


class MerchantVerificationView(APIView):
    """API endpoint for verifying a merchant"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        merchant = get_object_or_404(Merchant, pk=pk)
        serializer = MerchantVerificationSerializer(merchant, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Get risk assessment from ML model
            risk_data = assess_merchant_risk(merchant)
            
            # Get external verification data
            external_data = verify_merchant_external(merchant)
            
            # Update merchant with verification data
            merchant = serializer.save(
                verified_by=request.user,
                last_verified_at=timezone.now(),
                external_api_response=external_data
            )
            
            # Create audit log
            audit_details = {
                'status': merchant.status,
                'risk_level': merchant.risk_level,
                'risk_score': merchant.risk_score
            }
            AuditLog.objects.create(
                user=request.user,
                merchant=merchant,
                action='verify',
                details=audit_details
            )
            
            return Response({
                'merchant': MerchantSerializer(merchant).data,
                'risk_assessment': risk_data,
                'external_verification': external_data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionPatternView(APIView):
    """API endpoint for merchant transaction patterns"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, merchant_id):
        merchant = get_object_or_404(Merchant, pk=merchant_id)
        transaction_patterns = merchant.transaction_patterns.all().order_by('-analysis_date')
        serializer = TransactionPatternSerializer(transaction_patterns, many=True)
        return Response(serializer.data)
    
    def post(self, request, merchant_id):
        merchant = get_object_or_404(Merchant, pk=merchant_id)
        
        # Analyze transaction patterns
        transaction_data = analyze_transaction_patterns(merchant)
        
        # Create or update transaction pattern record
        transaction_pattern, created = TransactionPattern.objects.update_or_create(
            merchant=merchant,
            defaults={
                'average_transaction_amount': transaction_data.get('average_transaction_amount'),
                'monthly_transaction_volume': transaction_data.get('monthly_transaction_volume'),
                'high_risk_countries_percentage': transaction_data.get('high_risk_countries_percentage'),
                'unusual_hours_percentage': transaction_data.get('unusual_hours_percentage'),
                'similar_transactions_percentage': transaction_data.get('similar_transactions_percentage'),
                'chargeback_rate': transaction_data.get('chargeback_rate'),
                'transaction_data': transaction_data.get('detailed_data')
            }
        )
        
        serializer = TransactionPatternSerializer(transaction_pattern)
        return Response(serializer.data)


class FlagListView(generics.ListCreateAPIView):
    """API endpoint for listing and creating flags for a merchant"""
    serializer_class = VerificationFlagSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        merchant_id = self.kwargs.get('merchant_id')
        return VerificationFlag.objects.filter(merchant_id=merchant_id).order_by('-created_at')
    
    def perform_create(self, serializer):
        merchant_id = self.kwargs.get('merchant_id')
        merchant = get_object_or_404(Merchant, pk=merchant_id)
        flag = serializer.save(
            merchant=merchant,
            created_by=self.request.user
        )
        
        # Update merchant status to flagged if not rejected
        if merchant.status != 'rejected':
            merchant.status = 'flagged'
            merchant.save()
        
        # Create audit log
        audit_details = {
            'flag_type': flag.flag_type,
            'severity': flag.severity,
            'description': flag.description
        }
        AuditLog.objects.create(
            user=self.request.user,
            merchant=merchant,
            action='flag',
            details=audit_details
        )


class FlagDetailView(generics.RetrieveUpdateAPIView):
    """API endpoint for retrieving and updating a flag"""
    queryset = VerificationFlag.objects.all()
    serializer_class = VerificationFlagSerializer
    permission_classes = [permissions.IsAuthenticated]


class ResolveFlagView(APIView):
    """API endpoint for resolving a verification flag"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        flag = get_object_or_404(VerificationFlag, pk=pk)
        merchant = flag.merchant
        
        resolution_notes = request.data.get('resolution_notes', '')
        status_value = request.data.get('status', 'resolved')
        
        if status_value not in ['resolved', 'dismissed']:
            return Response(
                {'error': 'Invalid status value. Must be "resolved" or "dismissed".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update flag
        flag.status = status_value
        flag.resolved_by = request.user
        flag.resolved_at = timezone.now()
        flag.resolution_notes = resolution_notes
        flag.save()
        
        # Check if there are any more open flags
        open_flags = merchant.verification_flags.filter(
            status__in=['open', 'investigating']
        ).exists()
        
        # If no more open flags, update merchant status
        if not open_flags and merchant.status == 'flagged':
            merchant.status = 'verified'
            merchant.save()
        
        # Create audit log
        audit_details = {
            'flag_id': flag.id,
            'status': flag.status,
            'resolution_notes': flag.resolution_notes
        }
        AuditLog.objects.create(
            user=request.user,
            merchant=merchant,
            action='review',
            details=audit_details
        )
        
        serializer = VerificationFlagSerializer(flag)
        return Response(serializer.data)


class ReportListView(generics.ListCreateAPIView):
    """API endpoint for listing and creating reports for a merchant"""
    serializer_class = VerificationReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        merchant_id = self.kwargs.get('merchant_id')
        return VerificationReport.objects.filter(merchant_id=merchant_id).order_by('-report_date')
    
    def perform_create(self, serializer):
        merchant_id = self.kwargs.get('merchant_id')
        merchant = get_object_or_404(Merchant, pk=merchant_id)
        
        # Compile report data
        report_data = {
            'merchant_info': {
                'name': merchant.name,
                'business_type': merchant.business_type,
                'registration_number': merchant.registration_number,
                'status': merchant.status,
                'risk_level': merchant.risk_level,
                'risk_score': merchant.risk_score,
            },
            'verification_details': merchant.verification_data,
            'external_api_data': merchant.external_api_response,
        }
        
        # Add transaction pattern data if available
        try:
            transaction_pattern = merchant.transaction_patterns.latest('analysis_date')
            report_data['transaction_pattern'] = {
                'average_transaction_amount': str(transaction_pattern.average_transaction_amount),
                'monthly_transaction_volume': transaction_pattern.monthly_transaction_volume,
                'high_risk_countries_percentage': transaction_pattern.high_risk_countries_percentage,
                'chargeback_rate': transaction_pattern.chargeback_rate,
            }
        except TransactionPattern.DoesNotExist:
            report_data['transaction_pattern'] = None
        
        # Add flags
        flags = merchant.verification_flags.all().values(
            'flag_type', 'severity', 'status', 'description'
        )
        report_data['flags'] = list(flags)
        
        report = serializer.save(
            merchant=merchant,
            generated_by=self.request.user,
            report_data=report_data
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=self.request.user,
            merchant=merchant,
            action='report'
        )


class ReportDetailView(generics.RetrieveAPIView):
    """API endpoint for retrieving a report"""
    queryset = VerificationReport.objects.all()
    serializer_class = VerificationReportSerializer
    permission_classes = [permissions.IsAuthenticated]


class DashboardStatsView(APIView):
    """API endpoint for dashboard statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        total_merchants = Merchant.objects.count()
        verified_merchants = Merchant.objects.filter(status='verified').count()
        flagged_merchants = Merchant.objects.filter(status='flagged').count()
        pending_merchants = Merchant.objects.filter(status='pending').count()
        rejected_merchants = Merchant.objects.filter(status='rejected').count()
        
        # Recent merchants (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_merchants = Merchant.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Open flags
        open_flags = VerificationFlag.objects.filter(
            status__in=['open', 'investigating']
        ).count()
        
        # High risk merchants
        high_risk_merchants = Merchant.objects.filter(
            risk_level__in=['high', 'extreme']
        ).count()
        
        return Response({
            'total_merchants': total_merchants,
            'verified_merchants': verified_merchants,
            'flagged_merchants': flagged_merchants,
            'pending_merchants': pending_merchants,
            'rejected_merchants': rejected_merchants,
            'recent_merchants': recent_merchants,
            'open_flags': open_flags,
            'high_risk_merchants': high_risk_merchants
        })


class RiskDistributionView(APIView):
    """API endpoint for risk level distribution"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        risk_levels = Merchant.objects.filter(
            risk_level__isnull=False
        ).values('risk_level').annotate(
            count=Count('id')
        ).order_by('risk_level')
        
        return Response(risk_levels)


class BusinessTypeDistributionView(APIView):
    """API endpoint for business type distribution"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        business_types = Merchant.objects.values('business_type').annotate(
            count=Count('id')
        ).order_by('business_type')
        
        return Response(business_types)


class RiskAssessmentView(APIView):
    """API endpoint for assessing merchant risk"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Extract data from request
        merchant_data = request.data.get('merchant_data', {})
        
        if not merchant_data:
            return Response(
                {'error': 'No merchant data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If merchant_id is provided, get merchant from database
        merchant_id = merchant_data.get('id')
        if merchant_id:
            try:
                merchant = Merchant.objects.get(id=merchant_id)
            except Merchant.DoesNotExist:
                return Response(
                    {'error': f'Merchant with id {merchant_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Create a temporary merchant object for assessment
            merchant = Merchant(
                name=merchant_data.get('name', 'Unknown'),
                business_type=merchant_data.get('business_type', 'other'),
                website=merchant_data.get('website'),
                country=merchant_data.get('country'),
                # Add other fields as needed
            )
        
        # Assess risk
        risk_data = assess_merchant_risk(merchant)
        
        return Response(risk_data)
