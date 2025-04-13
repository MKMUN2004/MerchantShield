import json
import csv
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Avg, Sum, F
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import (
    Merchant, 
    TransactionPattern, 
    VerificationFlag, 
    VerificationReport,
    AuditLog
)
from .forms import (
    MerchantForm, 
    MerchantVerificationForm, 
    FlagMerchantForm,
    ResolveFlagForm,
    VerificationReportForm,
    MerchantFilterForm
)
from .ml_models.risk_assessment import assess_merchant_risk
from .ml_models.transaction_analysis import analyze_transaction_patterns
from .services.external_api import verify_merchant_external


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(request, merchant, action, details=None):
    """Create an audit log entry for merchant verification actions"""
    AuditLog.objects.create(
        user=request.user,
        merchant=merchant,
        action=action,
        ip_address=get_client_ip(request),
        details=details
    )


@login_required
def dashboard(request):
    """Dashboard view with verification statistics and charts"""
    # Statistics for dashboard
    total_merchants = Merchant.objects.count()
    verified_merchants = Merchant.objects.filter(status='verified').count()
    flagged_merchants = Merchant.objects.filter(status='flagged').count()
    pending_merchants = Merchant.objects.filter(status='pending').count()
    rejected_merchants = Merchant.objects.filter(status='rejected').count()
    
    # Get merchants by risk level
    risk_levels = Merchant.objects.filter(
        risk_level__isnull=False
    ).values('risk_level').annotate(
        count=Count('id')
    ).order_by('risk_level')
    
    # Recent merchants
    recent_merchants = Merchant.objects.all().order_by('-created_at')[:5]
    
    # Recent verification flags
    recent_flags = VerificationFlag.objects.filter(
        status='open'
    ).order_by('-created_at')[:5]
    
    # Business type distribution
    business_types = Merchant.objects.values('business_type').annotate(
        count=Count('id')
    ).order_by('business_type')
    
    context = {
        'total_merchants': total_merchants,
        'verified_merchants': verified_merchants,
        'flagged_merchants': flagged_merchants,
        'pending_merchants': pending_merchants,
        'rejected_merchants': rejected_merchants,
        'risk_levels': list(risk_levels),
        'recent_merchants': recent_merchants,
        'recent_flags': recent_flags,
        'business_types': list(business_types),
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def merchant_list(request):
    """List all merchants with filtering options"""
    filter_form = MerchantFilterForm(request.GET)
    merchants = Merchant.objects.all()
    
    # Apply filters if form is valid
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        if data.get('name'):
            merchants = merchants.filter(name__icontains=data['name'])
        
        if data.get('business_type'):
            merchants = merchants.filter(business_type=data['business_type'])
        
        if data.get('status'):
            merchants = merchants.filter(status=data['status'])
        
        if data.get('risk_level'):
            merchants = merchants.filter(risk_level=data['risk_level'])
        
        if data.get('country'):
            merchants = merchants.filter(country__icontains=data['country'])
        
        if data.get('date_from'):
            merchants = merchants.filter(created_at__gte=data['date_from'])
        
        if data.get('date_to'):
            merchants = merchants.filter(created_at__lte=data['date_to'])
    
    # Pagination
    paginator = Paginator(merchants.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'filter_form': filter_form,
        'page_obj': page_obj,
    }
    
    return render(request, 'merchant_list.html', context)


@login_required
def merchant_detail(request, merchant_id):
    """Display detailed information about a merchant"""
    merchant = get_object_or_404(Merchant, id=merchant_id)
    
    # Get the transaction pattern if it exists
    try:
        transaction_pattern = merchant.transaction_patterns.latest('analysis_date')
    except TransactionPattern.DoesNotExist:
        transaction_pattern = None
    
    # Get all verification flags
    flags = merchant.verification_flags.all().order_by('-created_at')
    
    # Get all verification reports
    reports = merchant.verification_reports.all().order_by('-report_date')
    
    # Get audit logs
    audit_logs = merchant.audit_logs.all().order_by('-timestamp')[:10]
    
    context = {
        'merchant': merchant,
        'transaction_pattern': transaction_pattern,
        'flags': flags,
        'reports': reports,
        'audit_logs': audit_logs,
    }
    
    return render(request, 'merchant_detail.html', context)


@login_required
def add_merchant(request):
    """Add a new merchant to the system"""
    if request.method == 'POST':
        form = MerchantForm(request.POST)
        if form.is_valid():
            merchant = form.save(commit=False)
            merchant.created_by = request.user
            merchant.status = 'pending'
            merchant.save()
            
            # Create audit log
            create_audit_log(request, merchant, 'create')
            
            messages.success(request, f"Merchant '{merchant.name}' has been added successfully.")
            return redirect('merchant_detail', merchant_id=merchant.id)
    else:
        form = MerchantForm()
    
    return render(request, 'add_merchant.html', {'form': form})


@login_required
def edit_merchant(request, merchant_id):
    """Edit an existing merchant"""
    merchant = get_object_or_404(Merchant, id=merchant_id)
    
    if request.method == 'POST':
        form = MerchantForm(request.POST, instance=merchant)
        if form.is_valid():
            form.save()
            
            # Create audit log
            create_audit_log(request, merchant, 'update')
            
            messages.success(request, f"Merchant '{merchant.name}' has been updated successfully.")
            return redirect('merchant_detail', merchant_id=merchant.id)
    else:
        form = MerchantForm(instance=merchant)
    
    return render(request, 'add_merchant.html', {'form': form, 'merchant': merchant})


@login_required
def verify_merchant(request, merchant_id):
    """Verify a merchant using ML and external API checks"""
    merchant = get_object_or_404(Merchant, id=merchant_id)
    
    if request.method == 'POST':
        form = MerchantVerificationForm(request.POST, instance=merchant)
        if form.is_valid():
            # Save but don't commit to database yet
            merchant_update = form.save(commit=False)
            
            # Call the risk assessment model to get risk score
            risk_data = assess_merchant_risk(merchant)
            merchant_update.risk_score = risk_data['risk_score']
            
            # Set the verified_by user and last_verified_at timestamp
            merchant_update.verified_by = request.user
            merchant_update.save()
            
            # Create audit log
            audit_details = {
                'risk_score': merchant_update.risk_score,
                'status': merchant_update.status,
                'risk_level': merchant_update.risk_level
            }
            create_audit_log(request, merchant, 'verify', audit_details)
            
            messages.success(request, f"Merchant '{merchant.name}' has been verified successfully.")
            return redirect('merchant_detail', merchant_id=merchant.id)
    else:
        # Get data from external API for verification
        external_data = verify_merchant_external(merchant)
        
        # Get risk assessment from ML model
        risk_data = assess_merchant_risk(merchant)
        
        # Analyze transaction patterns if available
        transaction_data = analyze_transaction_patterns(merchant)
        
        # Pre-populate the form with suggested values
        merchant.risk_level = risk_data['suggested_risk_level']
        merchant.external_api_response = external_data
        
        form = MerchantVerificationForm(instance=merchant)
    
    context = {
        'form': form,
        'merchant': merchant,
        'risk_data': risk_data,
        'external_data': external_data,
        'transaction_data': transaction_data
    }
    
    return render(request, 'verify_merchant.html', context)


@login_required
def flagged_merchants(request):
    """Display all merchants that have been flagged for review"""
    # Get all open flags
    flags = VerificationFlag.objects.filter(
        status__in=['open', 'investigating']
    ).select_related('merchant').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(flags, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'flagged_merchants.html', {'page_obj': page_obj})


@login_required
def flag_merchant(request, merchant_id):
    """Flag a merchant for review"""
    merchant = get_object_or_404(Merchant, id=merchant_id)
    
    if request.method == 'POST':
        form = FlagMerchantForm(request.POST)
        if form.is_valid():
            flag = form.save(commit=False)
            flag.merchant = merchant
            flag.created_by = request.user
            flag.save()
            
            # Update merchant status to flagged if it's not already rejected
            if merchant.status != 'rejected':
                merchant.status = 'flagged'
                merchant.save()
            
            # Create audit log
            audit_details = {
                'flag_type': flag.flag_type,
                'severity': flag.severity,
                'description': flag.description
            }
            create_audit_log(request, merchant, 'flag', audit_details)
            
            messages.success(request, f"Merchant '{merchant.name}' has been flagged for review.")
            return redirect('merchant_detail', merchant_id=merchant.id)
    else:
        form = FlagMerchantForm()
    
    return render(request, 'add_merchant.html', {
        'form': form,
        'merchant': merchant,
        'flag_form': True
    })


@login_required
def resolve_flag(request, flag_id):
    """Resolve a verification flag"""
    flag = get_object_or_404(VerificationFlag, id=flag_id)
    merchant = flag.merchant
    
    if request.method == 'POST':
        form = ResolveFlagForm(request.POST, instance=flag)
        if form.is_valid():
            flag = form.save(commit=False)
            flag.resolved_by = request.user
            flag.resolved_at = datetime.now()
            flag.save()
            
            # Check if there are any more open flags for this merchant
            open_flags = merchant.verification_flags.filter(
                status__in=['open', 'investigating']
            ).exists()
            
            # If no more open flags, update merchant status to verified
            if not open_flags and merchant.status == 'flagged':
                merchant.status = 'verified'
                merchant.save()
            
            # Create audit log
            audit_details = {
                'flag_id': flag.id,
                'flag_type': flag.flag_type,
                'status': flag.status,
                'resolution_notes': flag.resolution_notes
            }
            create_audit_log(request, merchant, 'review', audit_details)
            
            messages.success(request, f"Flag has been resolved successfully.")
            return redirect('flagged_merchants')
    else:
        form = ResolveFlagForm(instance=flag)
    
    return render(request, 'add_merchant.html', {
        'form': form,
        'merchant': merchant,
        'flag': flag,
        'resolve_form': True
    })


@login_required
def reports(request):
    """Display all verification reports"""
    reports = VerificationReport.objects.all().select_related(
        'merchant', 'generated_by'
    ).order_by('-report_date')
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'reports.html', {'page_obj': page_obj})


@login_required
def generate_report(request, merchant_id):
    """Generate a verification report for a merchant"""
    merchant = get_object_or_404(Merchant, id=merchant_id)
    
    if request.method == 'POST':
        form = VerificationReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.merchant = merchant
            report.generated_by = request.user
            
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
            
            report.report_data = report_data
            report.save()
            
            # Create audit log
            create_audit_log(request, merchant, 'report')
            
            messages.success(request, f"Verification report has been generated successfully.")
            return redirect('view_report', report_id=report.id)
    else:
        form = VerificationReportForm()
    
    return render(request, 'add_merchant.html', {
        'form': form,
        'merchant': merchant,
        'report_form': True
    })


@login_required
def view_report(request, report_id):
    """View a specific verification report"""
    report = get_object_or_404(VerificationReport, id=report_id)
    
    return render(request, 'reports.html', {
        'report': report,
        'view_single_report': True
    })


@login_required
def export_report(request, report_id):
    """Export a verification report as CSV"""
    report = get_object_or_404(VerificationReport, id=report_id)
    merchant = report.merchant
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="verification_report_{merchant.name}_{report.report_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Verification Report'])
    writer.writerow(['Generated on', report.report_date.strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Generated by', report.generated_by.username])
    writer.writerow([])
    
    # Merchant information
    writer.writerow(['Merchant Information'])
    writer.writerow(['Name', merchant.name])
    writer.writerow(['Business Type', merchant.get_business_type_display()])
    writer.writerow(['Registration Number', merchant.registration_number])
    writer.writerow(['Status', merchant.get_status_display()])
    writer.writerow(['Risk Level', merchant.get_risk_level_display() if merchant.risk_level else 'Not assessed'])
    writer.writerow(['Risk Score', merchant.risk_score if merchant.risk_score else 'Not assessed'])
    writer.writerow([])
    
    # Risk assessment
    writer.writerow(['Risk Assessment'])
    writer.writerow([report.risk_assessment])
    writer.writerow([])
    
    # Recommendations
    writer.writerow(['Recommendations'])
    writer.writerow([report.recommendations])
    writer.writerow([])
    
    # Flags
    flags = merchant.verification_flags.all()
    if flags:
        writer.writerow(['Verification Flags'])
        writer.writerow(['Type', 'Severity', 'Status', 'Description'])
        for flag in flags:
            writer.writerow([
                flag.get_flag_type_display(),
                flag.get_severity_display(),
                flag.get_status_display(),
                flag.description
            ])
    
    return response


@login_required
def search(request):
    """Search for merchants by name, registration number, or website"""
    query = request.GET.get('q', '')
    
    if query:
        merchants = Merchant.objects.filter(
            Q(name__icontains=query) |
            Q(registration_number__icontains=query) |
            Q(website__icontains=query) |
            Q(email__icontains=query)
        ).order_by('-created_at')
    else:
        merchants = Merchant.objects.none()
    
    # Pagination
    paginator = Paginator(merchants, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
    }
    
    return render(request, 'merchant_list.html', context)
