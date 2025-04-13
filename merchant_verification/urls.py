from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from .forms import LoginForm

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(
        template_name='login.html',
        authentication_form=LoginForm
    ), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Dashboard and home
    path('', views.dashboard, name='dashboard'),
    
    # Merchant management
    path('merchants/', views.merchant_list, name='merchant_list'),
    path('merchants/add/', views.add_merchant, name='add_merchant'),
    path('merchants/<int:merchant_id>/', views.merchant_detail, name='merchant_detail'),
    path('merchants/<int:merchant_id>/edit/', views.edit_merchant, name='edit_merchant'),
    path('merchants/<int:merchant_id>/verify/', views.verify_merchant, name='verify_merchant'),
    
    # Flags
    path('flags/', views.flagged_merchants, name='flagged_merchants'),
    path('merchants/<int:merchant_id>/flag/', views.flag_merchant, name='flag_merchant'),
    path('flags/<int:flag_id>/resolve/', views.resolve_flag, name='resolve_flag'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('merchants/<int:merchant_id>/generate-report/', views.generate_report, name='generate_report'),
    path('reports/<int:report_id>/view/', views.view_report, name='view_report'),
    path('reports/<int:report_id>/export/', views.export_report, name='export_report'),
    
    # Search
    path('search/', views.search, name='search'),
]
