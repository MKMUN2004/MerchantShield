from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Merchant, VerificationFlag, VerificationReport


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Username'}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Password'}
        )
    )


class MerchantForm(forms.ModelForm):
    class Meta:
        model = Merchant
        fields = [
            'name', 'business_type', 'registration_number', 'tax_id', 'website',
            'email', 'phone', 'address', 'city', 'state', 'country', 'postal_code'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_type': forms.Select(attrs={'class': 'form-select'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
        }


class MerchantVerificationForm(forms.ModelForm):
    class Meta:
        model = Merchant
        fields = ['status', 'risk_level', 'verification_data']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
            'verification_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class FlagMerchantForm(forms.ModelForm):
    class Meta:
        model = VerificationFlag
        fields = ['flag_type', 'description', 'severity']
        widgets = {
            'flag_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
        }


class ResolveFlagForm(forms.ModelForm):
    class Meta:
        model = VerificationFlag
        fields = ['status', 'resolution_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class VerificationReportForm(forms.ModelForm):
    class Meta:
        model = VerificationReport
        fields = ['risk_assessment', 'recommendations']
        widgets = {
            'risk_assessment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class MerchantFilterForm(forms.Form):
    name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    business_type = forms.ChoiceField(
        required=False,
        choices=[('', '--- All Business Types ---')] + Merchant.BUSINESS_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        required=False, 
        choices=[('', '--- All Statuses ---')] + Merchant.VERIFICATION_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    risk_level = forms.ChoiceField(
        required=False,
        choices=[('', '--- All Risk Levels ---')] + Merchant.RISK_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    country = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
