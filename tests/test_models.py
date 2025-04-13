import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from merchant_verification.models import (
    Merchant,
    TransactionPattern,
    VerificationFlag,
    VerificationReport,
    AuditLog
)


class MerchantModelTest(TestCase):
    """Test cases for the Merchant model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create a test merchant
        self.merchant = Merchant.objects.create(
            name='Test Merchant',
            business_type='retail',
            registration_number='TEST123456',
            tax_id='TAX123456',
            website='https://www.testmerchant.com',
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
    
    def test_merchant_creation(self):
        """Test that a merchant can be created with all fields"""
        self.assertEqual(self.merchant.name, 'Test Merchant')
        self.assertEqual(self.merchant.business_type, 'retail')
        self.assertEqual(self.merchant.registration_number, 'TEST123456')
        self.assertEqual(self.merchant.status, 'pending')
        self.assertIsNone(self.merchant.risk_level)
        self.assertIsNone(self.merchant.risk_score)
        self.assertEqual(self.merchant.created_by, self.user)
    
    def test_merchant_str_representation(self):
        """Test the string representation of a merchant"""
        expected_str = 'Test Merchant (Pending Verification)'
        self.assertEqual(str(self.merchant), expected_str)
    
    def test_merchant_verification(self):
        """Test that merchant verification updates timestamps"""
        self.assertIsNone(self.merchant.last_verified_at)
        
        # Update status to verified
        self.merchant.status = 'verified'
        self.merchant.verified_by = self.user
        self.merchant.save()
        
        # Check that last_verified_at is set
        self.assertIsNotNone(self.merchant.last_verified_at)
        self.assertEqual(self.merchant.verified_by, self.user)
    
    def test_merchant_risk_assessment(self):
        """Test merchant risk assessment fields"""
        # Assign risk level and score
        self.merchant.risk_level = 'medium'
        self.merchant.risk_score = 2.5
        self.merchant.save()
        
        # Reload from database
        merchant = Merchant.objects.get(id=self.merchant.id)
        self.assertEqual(merchant.risk_level, 'medium')
        self.assertEqual(merchant.risk_score, 2.5)


class TransactionPatternTest(TestCase):
    """Test cases for the TransactionPattern model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create a test merchant
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
        
        # Create a transaction pattern
        self.transaction_pattern = TransactionPattern.objects.create(
            merchant=self.merchant,
            average_transaction_amount=100.50,
            monthly_transaction_volume=500,
            high_risk_countries_percentage=5.0,
            unusual_hours_percentage=10.0,
            similar_transactions_percentage=25.0,
            chargeback_rate=0.5,
            transaction_data={
                'country_distribution': {
                    'USA': 300,
                    'Canada': 100,
                    'Mexico': 50,
                    'Germany': 50
                },
                'hourly_distribution': {
                    '9': 50,
                    '10': 75,
                    '11': 100,
                    '12': 125,
                    '13': 100,
                    '14': 50
                }
            }
        )
    
    def test_transaction_pattern_creation(self):
        """Test that a transaction pattern can be created"""
        self.assertEqual(self.transaction_pattern.merchant, self.merchant)
        self.assertEqual(self.transaction_pattern.average_transaction_amount, 100.50)
        self.assertEqual(self.transaction_pattern.monthly_transaction_volume, 500)
        self.assertEqual(self.transaction_pattern.high_risk_countries_percentage, 5.0)
        self.assertEqual(self.transaction_pattern.chargeback_rate, 0.5)
        self.assertIsNotNone(self.transaction_pattern.transaction_data)
    
    def test_transaction_pattern_str_representation(self):
        """Test the string representation of a transaction pattern"""
        expected_str = f"Transaction Pattern for {self.merchant.name}"
        self.assertEqual(str(self.transaction_pattern), expected_str)
    
    def test_transaction_pattern_json_data(self):
        """Test that transaction data is properly stored as JSON"""
        self.assertEqual(self.transaction_pattern.transaction_data['country_distribution']['USA'], 300)
        self.assertEqual(self.transaction_pattern.transaction_data['country_distribution']['Canada'], 100)
        self.assertEqual(self.transaction_pattern.transaction_data['hourly_distribution']['12'], 125)


class VerificationFlagTest(TestCase):
    """Test cases for the VerificationFlag model"""
    
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpassword'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpassword'
        )
        
        # Create a test merchant
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
            created_by=self.user1
        )
        
        # Create a verification flag
        self.flag = VerificationFlag.objects.create(
            merchant=self.merchant,
            flag_type='suspicious_website',
            description='Website contains suspicious gambling content.',
            severity='high',
            created_by=self.user1
        )
    
    def test_flag_creation(self):
        """Test that a verification flag can be created"""
        self.assertEqual(self.flag.merchant, self.merchant)
        self.assertEqual(self.flag.flag_type, 'suspicious_website')
        self.assertEqual(self.flag.severity, 'high')
        self.assertEqual(self.flag.status, 'open')  # Default status
        self.assertIsNone(self.flag.resolved_at)
        self.assertIsNone(self.flag.resolved_by)
    
    def test_flag_str_representation(self):
        """Test the string representation of a verification flag"""
        expected_str = f"Suspicious Website Content Flag for {self.merchant.name}"
        self.assertEqual(str(self.flag), expected_str)
    
    def test_resolve_flag(self):
        """Test that a flag can be resolved"""
        # Initially not resolved
        self.assertEqual(self.flag.status, 'open')
        self.assertIsNone(self.flag.resolved_at)
        self.assertIsNone(self.flag.resolved_by)
        
        # Resolve the flag
        resolution_notes = "Website was reviewed and found to be legitimate."
        self.flag.resolve(self.user2, resolution_notes)
        
        # Check that the flag is now resolved
        self.assertEqual(self.flag.status, 'resolved')
        self.assertIsNotNone(self.flag.resolved_at)
        self.assertEqual(self.flag.resolved_by, self.user2)
        self.assertEqual(self.flag.resolution_notes, resolution_notes)


class VerificationReportTest(TestCase):
    """Test cases for the VerificationReport model"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create a test merchant
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
            status='verified',
            risk_level='low',
            risk_score=1.5,
            created_by=self.user,
            verified_by=self.user
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
                },
                'verification_details': None,
                'external_api_data': None,
                'transaction_pattern': {
                    'average_transaction_amount': '75.25',
                    'monthly_transaction_volume': 350,
                    'high_risk_countries_percentage': 2.5,
                    'chargeback_rate': 0.2,
                },
                'flags': []
            },
            risk_assessment="Merchant is low risk based on business type and transaction patterns.",
            recommendations="Standard verification procedures. Periodic review of transaction patterns."
        )
    
    def test_report_creation(self):
        """Test that a verification report can be created"""
        self.assertEqual(self.report.merchant, self.merchant)
        self.assertEqual(self.report.generated_by, self.user)
        self.assertIsNotNone(self.report.report_date)
        self.assertEqual(self.report.risk_assessment, "Merchant is low risk based on business type and transaction patterns.")
        self.assertEqual(self.report.recommendations, "Standard verification procedures. Periodic review of transaction patterns.")
    
    def test_report_str_representation(self):
        """Test the string representation of a verification report"""
        expected_str = f"Verification Report for {self.merchant.name} ({self.report.report_date.date()})"
        self.assertEqual(str(self.report), expected_str)
    
    def test_report_json_data(self):
        """Test that report data is properly stored as JSON"""
        self.assertEqual(self.report.report_data['merchant_info']['name'], self.merchant.name)
        self.assertEqual(self.report.report_data['merchant_info']['risk_level'], 'low')
        self.assertEqual(self.report.report_data['transaction_pattern']['average_transaction_amount'], '75.25')
        self.assertEqual(self.report.report_data['transaction_pattern']['monthly_transaction_volume'], 350)


class AuditLogTest(TestCase):
    """Test cases for the AuditLog model"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create a test merchant
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
        
        # Create an audit log entry
        self.audit_log = AuditLog.objects.create(
            user=self.user,
            merchant=self.merchant,
            action='create',
            ip_address='127.0.0.1',
            details={
                'fields_updated': ['name', 'registration_number', 'email']
            }
        )
    
    def test_audit_log_creation(self):
        """Test that an audit log entry can be created"""
        self.assertEqual(self.audit_log.user, self.user)
        self.assertEqual(self.audit_log.merchant, self.merchant)
        self.assertEqual(self.audit_log.action, 'create')
        self.assertEqual(self.audit_log.ip_address, '127.0.0.1')
        self.assertIsNotNone(self.audit_log.details)
    
    def test_audit_log_str_representation(self):
        """Test the string representation of an audit log"""
        expected_str = f"Create Merchant by {self.user} on {self.merchant.name}"
        self.assertEqual(str(self.audit_log), expected_str)
    
    def test_audit_log_json_data(self):
        """Test that audit log details are properly stored as JSON"""
        self.assertEqual(self.audit_log.details['fields_updated'], ['name', 'registration_number', 'email'])
