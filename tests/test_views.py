import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from merchant_verification.models import (
    Merchant,
    TransactionPattern,
    VerificationFlag,
    VerificationReport,
    AuditLog
)


class ViewsTestCase(TestCase):
    """Test cases for views in the merchant verification app"""
    
    def setUp(self):
        # Create a test client
        self.client = Client()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test merchant
        self.merchant = Merchant.objects.create(
            name='Test Merchant',
            business_type='retail',
            registration_number='TEST123456',
            email='info@testmerchant.com',
            phone='+1234567890',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            country='Test Country',
            postal_code='12345',
            status='pending',
            created_by=self.user
        )
        
        # Create a verification flag
        self.flag = VerificationFlag.objects.create(
            merchant=self.merchant,
            flag_type='suspicious_website',
            description='Website contains suspicious content.',
            severity='medium',
            created_by=self.user
        )
        
        # Create a verification report
        self.report = VerificationReport.objects.create(
            merchant=self.merchant,
            generated_by=self.user,
            report_data={
                'merchant_info': {
                    'name': self.merchant.name,
                    'business_type': self.merchant.business_type,
                    'registration_number': self.merchant.registration_number,
                    'status': self.merchant.status,
                    'risk_level': self.merchant.risk_level,
                    'risk_score': self.merchant.risk_score,
                }
            },
            risk_assessment="Test risk assessment",
            recommendations="Test recommendations"
        )
        
        # Log in the test user
        self.client.login(username='testuser', password='testpassword')
    
    def test_dashboard_view(self):
        """Test the dashboard view"""
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(response, 'Dashboard')
        
        # Check that the dashboard contains expected data
        self.assertIn('total_merchants', response.context)
        self.assertIn('verified_merchants', response.context)
        self.assertIn('flagged_merchants', response.context)
        self.assertIn('pending_merchants', response.context)
        self.assertIn('rejected_merchants', response.context)
    
    def test_merchant_list_view(self):
        """Test the merchant list view"""
        response = self.client.get(reverse('merchant_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'merchant_list.html')
        self.assertContains(response, 'Merchant List')
        
        # Check that the merchant list contains our test merchant
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0].name, 'Test Merchant')
    
    def test_merchant_detail_view(self):
        """Test the merchant detail view"""
        response = self.client.get(reverse('merchant_detail', args=[self.merchant.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'merchant_detail.html')
        self.assertContains(response, 'Test Merchant')
        
        # Check that the context contains the merchant
        self.assertEqual(response.context['merchant'], self.merchant)
        
        # Check that flags are in the context
        self.assertIn('flags', response.context)
        self.assertEqual(len(response.context['flags']), 1)
        self.assertEqual(response.context['flags'][0], self.flag)
        
        # Check that reports are in the context
        self.assertIn('reports', response.context)
        self.assertEqual(len(response.context['reports']), 1)
        self.assertEqual(response.context['reports'][0], self.report)
    
    def test_add_merchant_view_get(self):
        """Test GET request to the add merchant view"""
        response = self.client.get(reverse('add_merchant'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_merchant.html')
        self.assertContains(response, 'Add New Merchant')
        
        # Check that a form is in the context
        self.assertIn('form', response.context)
    
    def test_add_merchant_view_post(self):
        """Test POST request to the add merchant view"""
        merchant_data = {
            'name': 'New Test Merchant',
            'business_type': 'service',
            'registration_number': 'NEW123456',
            'tax_id': 'TAX987654',
            'website': 'https://www.newtestmerchant.com',
            'email': 'info@newtestmerchant.com',
            'phone': '+9876543210',
            'address': '456 New Street',
            'city': 'New City',
            'state': 'New State',
            'country': 'New Country',
            'postal_code': '54321'
        }
        
        response = self.client.post(reverse('add_merchant'), merchant_data, follow=True)
        
        # Check that the merchant was created
        self.assertEqual(response.status_code, 200)
        
        # Check that we were redirected to the merchant detail page
        self.assertTemplateUsed(response, 'merchant_detail.html')
        
        # Verify the new merchant was created in the database
        new_merchant = Merchant.objects.get(name='New Test Merchant')
        self.assertEqual(new_merchant.business_type, 'service')
        self.assertEqual(new_merchant.registration_number, 'NEW123456')
        self.assertEqual(new_merchant.status, 'pending')  # Default status
        self.assertEqual(new_merchant.created_by, self.user)
    
    def test_edit_merchant_view(self):
        """Test the edit merchant view"""
        response = self.client.get(reverse('edit_merchant', args=[self.merchant.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_merchant.html')
        self.assertContains(response, 'Edit Merchant')
        
        # Check that the form is pre-populated with merchant data
        self.assertEqual(response.context['form'].instance, self.merchant)
    
    def test_verify_merchant_view(self):
        """Test the verify merchant view"""
        response = self.client.get(reverse('verify_merchant', args=[self.merchant.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'verify_merchant.html')
        self.assertContains(response, 'Verify Merchant')
        
        # Check that verification data is in the context
        self.assertIn('risk_data', response.context)
        self.assertIn('external_data', response.context)
        self.assertIn('transaction_data', response.context)
    
    def test_flag_merchant_view(self):
        """Test the flag merchant view"""
        response = self.client.get(reverse('flag_merchant', args=[self.merchant.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_merchant.html')
        self.assertContains(response, 'Flag Merchant')
        
        # Check that a form is in the context
        self.assertIn('form', response.context)
        
        # Submit a flag
        flag_data = {
            'flag_type': 'missing_info',
            'description': 'Missing critical business registration information.',
            'severity': 'high'
        }
        
        response = self.client.post(reverse('flag_merchant', args=[self.merchant.id]), flag_data, follow=True)
        
        # Check that the flag was created
        self.assertEqual(response.status_code, 200)
        
        # Verify the flag was created in the database
        flags = VerificationFlag.objects.filter(merchant=self.merchant, flag_type='missing_info')
        self.assertTrue(flags.exists())
        self.assertEqual(flags[0].severity, 'high')
        self.assertEqual(flags[0].description, 'Missing critical business registration information.')
        
        # Check that the merchant status was updated to flagged
        self.merchant.refresh_from_db()
        self.assertEqual(self.merchant.status, 'flagged')
    
    def test_resolve_flag_view(self):
        """Test the resolve flag view"""
        response = self.client.get(reverse('resolve_flag', args=[self.flag.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_merchant.html')
        self.assertContains(response, 'Resolve Flag')
        
        # Check that a form is in the context
        self.assertIn('form', response.context)
        
        # Submit a resolution
        resolution_data = {
            'status': 'resolved',
            'resolution_notes': 'Website was reviewed and found to be legitimate.'
        }
        
        response = self.client.post(reverse('resolve_flag', args=[self.flag.id]), resolution_data, follow=True)
        
        # Check that the flag was resolved
        self.assertEqual(response.status_code, 200)
        
        # Verify the flag was updated in the database
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, 'resolved')
        self.assertEqual(self.flag.resolution_notes, 'Website was reviewed and found to be legitimate.')
        self.assertEqual(self.flag.resolved_by, self.user)
    
    def test_generate_report_view(self):
        """Test the generate report view"""
        response = self.client.get(reverse('generate_report', args=[self.merchant.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_merchant.html')
        self.assertContains(response, 'Generate Report')
        
        # Check that a form is in the context
        self.assertIn('form', response.context)
        
        # Submit a report
        report_data = {
            'risk_assessment': 'This merchant has a moderate risk profile.',
            'recommendations': 'Monitor transaction patterns and re-evaluate in 30 days.'
        }
        
        response = self.client.post(reverse('generate_report', args=[self.merchant.id]), report_data, follow=True)
        
        # Check that the report was created
        self.assertEqual(response.status_code, 200)
        
        # Verify the report was created in the database
        reports = VerificationReport.objects.filter(
            merchant=self.merchant,
            risk_assessment='This merchant has a moderate risk profile.'
        )
        self.assertTrue(reports.exists())
        self.assertEqual(reports[0].recommendations, 'Monitor transaction patterns and re-evaluate in 30 days.')
        self.assertEqual(reports[0].generated_by, self.user)
    
    def test_view_report_view(self):
        """Test the view report view"""
        response = self.client.get(reverse('view_report', args=[self.report.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports.html')
        
        # Check that the report is in the context
        self.assertIn('report', response.context)
        self.assertEqual(response.context['report'], self.report)
        self.assertTrue(response.context['view_single_report'])
    
    def test_export_report_view(self):
        """Test the export report view"""
        response = self.client.get(reverse('export_report', args=[self.report.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue('attachment' in response['Content-Disposition'])
    
    def test_flagged_merchants_view(self):
        """Test the flagged merchants view"""
        # First mark the merchant as flagged
        self.merchant.status = 'flagged'
        self.merchant.save()
        
        response = self.client.get(reverse('flagged_merchants'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flagged_merchants.html')
        self.assertContains(response, 'Flagged Merchants')
        
        # Check that flags are in the context
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)
    
    def test_reports_view(self):
        """Test the reports view"""
        response = self.client.get(reverse('reports'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports.html')
        self.assertContains(response, 'Verification Reports')
        
        # Check that reports are in the context
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)
    
    def test_search_view(self):
        """Test the search view"""
        # Search for our test merchant
        response = self.client.get(reverse('search'), {'q': 'Test'})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'merchant_list.html')
        
        # Check that the search found our merchant
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0].name, 'Test Merchant')
        
        # Search for non-existent merchant
        response = self.client.get(reverse('search'), {'q': 'NonExistent'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 0)
    
    def test_login_required(self):
        """Test that views require login"""
        # Logout the test user
        self.client.logout()
        
        # Try to access protected views
        views_to_test = [
            reverse('dashboard'),
            reverse('merchant_list'),
            reverse('merchant_detail', args=[self.merchant.id]),
            reverse('add_merchant'),
            reverse('edit_merchant', args=[self.merchant.id]),
            reverse('verify_merchant', args=[self.merchant.id]),
            reverse('flag_merchant', args=[self.merchant.id]),
            reverse('flagged_merchants'),
            reverse('reports')
        ]
        
        for view_url in views_to_test:
            response = self.client.get(view_url)
            # Should redirect to login page
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/login/'))
