import pytest
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from merchant_verification.models import (
    Merchant,
    TransactionPattern,
    VerificationFlag,
    VerificationReport
)


class APITestCase(TestCase):
    """Test cases for the API endpoints"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test merchants
        self.merchant1 = Merchant.objects.create(
            name='Test Merchant 1',
            business_type='retail',
            registration_number='TEST123456',
            email='info@test1.com',
            phone='+1234567890',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            country='United States',
            postal_code='12345',
            status='verified',
            risk_level='low',
            risk_score=1.5,
            created_by=self.user,
            verified_by=self.user
        )
        
        self.merchant2 = Merchant.objects.create(
            name='Test Merchant 2',
            business_type='online',
            registration_number='TEST654321',
            email='info@test2.com',
            phone='+0987654321',
            address='456 Test Street',
            city='Test City',
            state='Test State',
            country='Canada',
            postal_code='54321',
            status='flagged',
            risk_level='high',
            risk_score=3.7,
            created_by=self.user
        )
        
        # Create a verification flag
        self.flag = VerificationFlag.objects.create(
            merchant=self.merchant2,
            flag_type='suspicious_website',
            description='Website contains suspicious content.',
            severity='high',
            created_by=self.user
        )
        
        # Create a transaction pattern
        self.transaction_pattern = TransactionPattern.objects.create(
            merchant=self.merchant1,
            average_transaction_amount=125.00,
            monthly_transaction_volume=500,
            high_risk_countries_percentage=2.0,
            unusual_hours_percentage=5.0,
            similar_transactions_percentage=15.0,
            chargeback_rate=0.2
        )
        
        # Create a verification report
        self.report = VerificationReport.objects.create(
            merchant=self.merchant1,
            generated_by=self.user,
            report_data={
                'merchant_info': {
                    'name': self.merchant1.name,
                    'business_type': self.merchant1.business_type,
                    'registration_number': self.merchant1.registration_number,
                    'status': self.merchant1.status,
                    'risk_level': self.merchant1.risk_level,
                    'risk_score': self.merchant1.risk_score,
                }
            },
            risk_assessment="Low risk merchant with good transaction history.",
            recommendations="Continue standard monitoring."
        )
        
        # Create API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_merchant_list_api(self):
        """Test the merchant list API endpoint"""
        response = self.client.get(reverse('api_merchant_list'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that we get both merchants
        self.assertEqual(len(data), 2)
        
        # Verify the data for the first merchant
        merchant1_data = next(m for m in data if m['name'] == 'Test Merchant 1')
        self.assertEqual(merchant1_data['business_type'], 'retail')
        self.assertEqual(merchant1_data['status'], 'verified')
        self.assertEqual(merchant1_data['risk_level'], 'low')
        self.assertEqual(merchant1_data['country'], 'United States')
        
        # Test filtering
        response = self.client.get(reverse('api_merchant_list') + '?status=flagged')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Merchant 2')
    
    def test_merchant_detail_api(self):
        """Test the merchant detail API endpoint"""
        response = self.client.get(reverse('api_merchant_detail', args=[self.merchant1.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the merchant data
        self.assertEqual(data['name'], 'Test Merchant 1')
        self.assertEqual(data['business_type'], 'retail')
        self.assertEqual(data['status'], 'verified')
        self.assertEqual(data['risk_level'], 'low')
        self.assertEqual(data['risk_score'], 1.5)
        
        # Check that transaction patterns are included
        self.assertTrue('transaction_patterns' in data)
        self.assertEqual(len(data['transaction_patterns']), 1)
        self.assertEqual(data['transaction_patterns'][0]['average_transaction_amount'], '125.00')
    
    def test_merchant_verification_api(self):
        """Test the merchant verification API endpoint"""
        verification_data = {
            'status': 'verified',
            'risk_level': 'medium',
            'risk_score': 2.5,
            'verification_data': {
                'notes': 'Merchant verified via phone call and document check.'
            }
        }
        
        response = self.client.post(
            reverse('api_merchant_verify', args=[self.merchant2.id]),
            verification_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the response
        self.assertTrue('merchant' in data)
        self.assertTrue('risk_assessment' in data)
        self.assertTrue('external_verification' in data)
        
        # Check that the merchant was updated
        self.merchant2.refresh_from_db()
        self.assertEqual(self.merchant2.status, 'verified')
        self.assertEqual(self.merchant2.risk_level, 'medium')
        self.assertEqual(self.merchant2.risk_score, 2.5)
        self.assertEqual(self.merchant2.verified_by, self.user)
    
    def test_transaction_pattern_api(self):
        """Test the transaction pattern API endpoint"""
        # Get transaction patterns
        response = self.client.get(reverse('api_transaction_patterns', args=[self.merchant1.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['average_transaction_amount'], '125.00')
        self.assertEqual(data[0]['monthly_transaction_volume'], 500)
        self.assertEqual(data[0]['chargeback_rate'], 0.2)
        
        # Analyze transaction patterns
        response = self.client.post(reverse('api_transaction_patterns', args=[self.merchant2.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify that a new pattern was created
        self.assertTrue('average_transaction_amount' in data)
        self.assertTrue('monthly_transaction_volume' in data)
        self.assertTrue('high_risk_countries_percentage' in data)
        
        # Check that the pattern was saved to the database
        patterns = TransactionPattern.objects.filter(merchant=self.merchant2)
        self.assertTrue(patterns.exists())
    
    def test_flag_list_api(self):
        """Test the flag list API endpoint"""
        response = self.client.get(reverse('api_merchant_flags', args=[self.merchant2.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['flag_type'], 'suspicious_website')
        self.assertEqual(data[0]['severity'], 'high')
        self.assertEqual(data[0]['status'], 'open')
        
        # Create a new flag
        flag_data = {
            'flag_type': 'missing_info',
            'description': 'Missing important business registration documents.',
            'severity': 'medium'
        }
        
        response = self.client.post(
            reverse('api_merchant_flags', args=[self.merchant1.id]),
            flag_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Check that the flag was created
        flags = VerificationFlag.objects.filter(
            merchant=self.merchant1,
            flag_type='missing_info'
        )
        self.assertTrue(flags.exists())
        
        # Check that merchant1 status was updated to flagged
        self.merchant1.refresh_from_db()
        self.assertEqual(self.merchant1.status, 'flagged')
    
    def test_flag_detail_api(self):
        """Test the flag detail API endpoint"""
        response = self.client.get(reverse('api_flag_detail', args=[self.flag.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the data
        self.assertEqual(data['flag_type'], 'suspicious_website')
        self.assertEqual(data['severity'], 'high')
        self.assertEqual(data['status'], 'open')
        
        # Update the flag
        update_data = {
            'severity': 'critical',
            'description': 'Updated: Website contains highly suspicious content related to gambling.'
        }
        
        response = self.client.patch(
            reverse('api_flag_detail', args=[self.flag.id]),
            update_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that the flag was updated
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.severity, 'critical')
        self.assertEqual(self.flag.description, 'Updated: Website contains highly suspicious content related to gambling.')
    
    def test_resolve_flag_api(self):
        """Test the resolve flag API endpoint"""
        resolution_data = {
            'status': 'resolved',
            'resolution_notes': 'Website was thoroughly reviewed and found to be legitimate.'
        }
        
        response = self.client.post(
            reverse('api_resolve_flag', args=[self.flag.id]),
            resolution_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that the flag was resolved
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, 'resolved')
        self.assertEqual(self.flag.resolution_notes, 'Website was thoroughly reviewed and found to be legitimate.')
        self.assertEqual(self.flag.resolved_by, self.user)
    
    def test_report_list_api(self):
        """Test the report list API endpoint"""
        response = self.client.get(reverse('api_merchant_reports', args=[self.merchant1.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['risk_assessment'], 'Low risk merchant with good transaction history.')
        self.assertEqual(data[0]['recommendations'], 'Continue standard monitoring.')
        
        # Create a new report
        report_data = {
            'risk_assessment': 'The merchant has a clean transaction history.',
            'recommendations': 'Periodic review every 90 days.'
        }
        
        response = self.client.post(
            reverse('api_merchant_reports', args=[self.merchant1.id]),
            report_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Check that the report was created
        reports = VerificationReport.objects.filter(
            merchant=self.merchant1,
            risk_assessment='The merchant has a clean transaction history.'
        )
        self.assertTrue(reports.exists())
    
    def test_report_detail_api(self):
        """Test the report detail API endpoint"""
        response = self.client.get(reverse('api_report_detail', args=[self.report.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the data
        self.assertEqual(data['risk_assessment'], 'Low risk merchant with good transaction history.')
        self.assertEqual(data['recommendations'], 'Continue standard monitoring.')
        self.assertTrue('merchant' in data)
        self.assertTrue('report_data' in data)
    
    def test_dashboard_stats_api(self):
        """Test the dashboard stats API endpoint"""
        response = self.client.get(reverse('api_dashboard_stats'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the stats
        self.assertEqual(data['total_merchants'], 2)
        self.assertEqual(data['verified_merchants'], 1)
        self.assertEqual(data['flagged_merchants'], 1)
        self.assertEqual(data['pending_merchants'], 0)
        self.assertEqual(data['high_risk_merchants'], 1)
    
    def test_risk_assessment_api(self):
        """Test the risk assessment API endpoint"""
        merchant_data = {
            'merchant_data': {
                'name': 'API Test Merchant',
                'business_type': 'gambling',
                'website': 'https://www.testcasino.com',
                'country': 'Malta'
            }
        }
        
        response = self.client.post(
            reverse('api_assess_risk'),
            merchant_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify that risk assessment was performed
        self.assertTrue('risk_score' in data)
        self.assertTrue('risk_level' in data)
        self.assertTrue('risk_factors' in data)
        self.assertTrue('recommendations' in data)
        
        # For gambling business type, risk should be higher
        self.assertGreaterEqual(data['risk_score'], 3.0)
    
    def test_authentication_required(self):
        """Test that API endpoints require authentication"""
        # Create unauthenticated client
        client = APIClient()
        
        # Try to access protected endpoints
        endpoints_to_test = [
            reverse('api_merchant_list'),
            reverse('api_merchant_detail', args=[self.merchant1.id]),
            reverse('api_merchant_verify', args=[self.merchant1.id]),
            reverse('api_transaction_patterns', args=[self.merchant1.id]),
            reverse('api_merchant_flags', args=[self.merchant1.id]),
            reverse('api_dashboard_stats')
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            # Should return 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403])
