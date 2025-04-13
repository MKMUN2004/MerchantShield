from django.urls import path
from . import views

urlpatterns = [
    # Merchant endpoints
    path('merchants/', views.MerchantListView.as_view(), name='api_merchant_list'),
    path('merchants/<int:pk>/', views.MerchantDetailView.as_view(), name='api_merchant_detail'),
    path('merchants/<int:pk>/verify/', views.MerchantVerificationView.as_view(), name='api_merchant_verify'),
    
    # Transaction patterns
    path('merchants/<int:merchant_id>/transactions/', views.TransactionPatternView.as_view(), name='api_transaction_patterns'),
    
    # Flags
    path('merchants/<int:merchant_id>/flags/', views.FlagListView.as_view(), name='api_merchant_flags'),
    path('flags/<int:pk>/', views.FlagDetailView.as_view(), name='api_flag_detail'),
    path('flags/<int:pk>/resolve/', views.ResolveFlagView.as_view(), name='api_resolve_flag'),
    
    # Reports
    path('merchants/<int:merchant_id>/reports/', views.ReportListView.as_view(), name='api_merchant_reports'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='api_report_detail'),
    
    # Dashboard data
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='api_dashboard_stats'),
    path('dashboard/risk-distribution/', views.RiskDistributionView.as_view(), name='api_risk_distribution'),
    path('dashboard/business-types/', views.BusinessTypeDistributionView.as_view(), name='api_business_types'),
    
    # Risk assessment
    path('assess-risk/', views.RiskAssessmentView.as_view(), name='api_assess_risk'),
]
