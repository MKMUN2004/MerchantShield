import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from merchant_verification.models import Merchant, TransactionPattern
from merchant_verification.ml_models.risk_assessment import (
    assess_merchant_risk,
    analyze_website_risk,
    assess_information_completeness,
    assess_transaction_risk,
    determine_risk_level,
    identify_high_risk_flags,
    generate_recommendations
)
from merchant_verification.ml_models.transaction_analysis import (
    analyze_transaction_patterns,
    generate_simulated_transactions,
    cluster_transaction_amounts
)


class RiskAssessmentTests(TestCase):
    """Test cases for the risk assessment ML model functions"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create low-risk merchant
        self.low_risk_merchant = Merchant.objects.create(
            name='Low Risk Shop',
            business_type='retail',
            registration_number='LR123456',
            tax_id='TAX123456',
            website='https://www.lowriskshop.com',
            email='info@lowriskshop.com',
            phone='+1234567890',
            address='123 Safe Street',
            city='Safe City',
            state='Safe State',
            country='Canada',
            postal_code='12345',
            status='pending',
            created_by=self.user
        )
        
        # Create high-risk merchant
        self.high_risk_merchant = Merchant.objects.create(
            name='High Risk Casino',
            business_type='gambling',
            registration_number='HR654321',
            tax_id='',  # Missing tax ID
            website='https://www.highriskcasino.bet',
            email='info@highriskcasino.bet',
            phone='+0987654321',
            address='456 Risk Street',
            city='Risk City',
            state='Risk State',
            country='Malta',
            postal_code='54321',
            status='pending',
            created_by=self.user
        )
        
        # Create incomplete merchant
        self.incomplete_merchant = Merchant.objects.create(
            name='Incomplete Business',
            business_type='other',
            registration_number='',  # Missing registration
            tax_id='',  # Missing tax ID
            website='',  # Missing website
            email='incomplete@example.com',
            phone='',  # Missing phone
            address='',  # Missing address
            city='',  # Missing city
            state='',  # Missing state
            country='Unknown',
            postal_code='',  # Missing postal code
            status='pending',
            created_by=self.user
        )
        
        # Create a transaction pattern for the low-risk merchant
        self.low_risk_transaction = TransactionPattern.objects.create(
            merchant=self.low_risk_merchant,
            average_transaction_amount=75.50,
            monthly_transaction_volume=500,
            high_risk_countries_percentage=1.0,
            unusual_hours_percentage=5.0,
            similar_transactions_percentage=20.0,
            chargeback_rate=0.2
        )
        
        # Create a transaction pattern for the high-risk merchant
        self.high_risk_transaction = TransactionPattern.objects.create(
            merchant=self.high_risk_merchant,
            average_transaction_amount=200.00,
            monthly_transaction_volume=2000,
            high_risk_countries_percentage=30.0,
            unusual_hours_percentage=25.0,
            similar_transactions_percentage=75.0,
            chargeback_rate=3.5
        )
    
    def test_assess_merchant_risk(self):
        """Test the main risk assessment function"""
        # Test low-risk merchant
        low_risk_assessment = assess_merchant_risk(self.low_risk_merchant)
        
        self.assertIsNotNone(low_risk_assessment)
        self.assertTrue('risk_score' in low_risk_assessment)
        self.assertTrue('risk_level' in low_risk_assessment)
        self.assertTrue('risk_factors' in low_risk_assessment)
        
        # Low-risk merchant should have lower risk score
        self.assertLess(low_risk_assessment['risk_score'], 3.0)
        
        # Test high-risk merchant
        high_risk_assessment = assess_merchant_risk(self.high_risk_merchant)
        
        self.assertIsNotNone(high_risk_assessment)
        self.assertTrue('risk_score' in high_risk_assessment)
        self.assertTrue('risk_level' in high_risk_assessment)
        self.assertTrue('risk_factors' in high_risk_assessment)
        
        # High-risk merchant should have higher risk score
        self.assertGreater(high_risk_assessment['risk_score'], 3.0)
        
        # Check that all risk factors are included
        expected_factors = [
            'business_type_risk', 'country_risk', 'website_risk',
            'completeness_risk', 'business_age_risk', 'transaction_risk'
        ]
        
        for factor in expected_factors:
            self.assertIn(factor, low_risk_assessment['risk_factors'])
            self.assertIn(factor, high_risk_assessment['risk_factors'])
        
        # Test incomplete merchant
        incomplete_assessment = assess_merchant_risk(self.incomplete_merchant)
        
        self.assertIsNotNone(incomplete_assessment)
        # Incomplete merchant should have high completeness risk
        self.assertGreater(incomplete_assessment['risk_factors']['completeness_risk'], 3.5)
    
    def test_analyze_website_risk(self):
        """Test the website risk analysis function"""
        # Test a standard retail website
        retail_risk = analyze_website_risk('https://www.normalstore.com')
        self.assertLess(retail_risk, 3.0)  # Should be low to moderate risk
        
        # Test a gambling website
        gambling_risk = analyze_website_risk('https://www.betcasino.com')
        self.assertGreaterEqual(gambling_risk, 4.0)  # Should be high risk
        
        # Test a gambling TLD
        gambling_tld_risk = analyze_website_risk('https://www.betting.bet')
        self.assertGreaterEqual(gambling_tld_risk, 4.0)  # Should be high risk
        
        # Test no website
        no_website_risk = analyze_website_risk(None)
        self.assertEqual(no_website_risk, 3.0)  # Should be moderate risk
    
    def test_assess_information_completeness(self):
        """Test the information completeness assessment function"""
        # Complete merchant should have low completeness risk
        complete_risk = assess_information_completeness(self.low_risk_merchant)
        self.assertLess(complete_risk, 2.0)
        
        # Incomplete merchant should have high completeness risk
        incomplete_risk = assess_information_completeness(self.incomplete_merchant)
        self.assertGreater(incomplete_risk, 4.0)
    
    def test_assess_transaction_risk(self):
        """Test the transaction risk assessment function"""
        # Low-risk transaction should have low risk score
        low_transaction_risk = assess_transaction_risk(self.low_risk_transaction)
        self.assertLess(low_transaction_risk, 2.5)
        
        # High-risk transaction should have high risk score
        high_transaction_risk = assess_transaction_risk(self.high_risk_transaction)
        self.assertGreater(high_transaction_risk, 3.5)
    
    def test_determine_risk_level(self):
        """Test the risk level determination function"""
        self.assertEqual(determine_risk_level(1.5), 'low')
        self.assertEqual(determine_risk_level(2.5), 'medium')
        self.assertEqual(determine_risk_level(3.5), 'high')
        self.assertEqual(determine_risk_level(4.5), 'extreme')
    
    def test_identify_high_risk_flags(self):
        """Test the high-risk flag identification function"""
        # Define mock risk factors
        high_risk_factors = {
            'business_type_risk': 5.0,  # Gambling
            'country_risk': 4.0,  # High-risk country
            'website_risk': 4.5,  # Gambling website
            'completeness_risk': 2.0,  # Complete information
            'transaction_risk': 4.0   # Suspicious transactions
        }
        
        # Identify flags for high-risk merchant
        flags = identify_high_risk_flags(high_risk_factors, self.high_risk_merchant)
        
        # Should identify multiple flags
        self.assertGreater(len(flags), 2)
        
        # Should include gambling flag
        self.assertTrue(any('gambling' in flag.lower() for flag in flags))
    
    def test_generate_recommendations(self):
        """Test the recommendation generation function"""
        # Recommendations for low-risk merchant
        low_recommendations = generate_recommendations('low', {}, self.low_risk_merchant)
        
        # Should include standard procedures
        self.assertTrue(any('standard' in rec.lower() for rec in low_recommendations))
        
        # Recommendations for high-risk merchant
        high_recommendations = generate_recommendations('high', {}, self.high_risk_merchant)
        
        # Should include enhanced due diligence
        self.assertTrue(any('enhanced due diligence' in rec.lower() for rec in high_recommendations))
        
        # Should include license verification for gambling business
        self.assertTrue(any('license' in rec.lower() for rec in high_recommendations))


class TransactionAnalysisTests(TestCase):
    """Test cases for the transaction analysis ML model functions"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create merchants
        self.retail_merchant = Merchant.objects.create(
            name='Retail Store',
            business_type='retail',
            registration_number='RT123456',
            email='info@retailstore.com',
            phone='+1234567890',
            address='123 Retail Street',
            city='Retail City',
            state='Retail State',
            country='United States',
            postal_code='12345',
            status='verified',
            created_by=self.user
        )
        
        self.gambling_merchant = Merchant.objects.create(
            name='Online Casino',
            business_type='gambling',
            registration_number='GA654321',
            email='info@onlinecasino.com',
            phone='+0987654321',
            address='456 Casino Street',
            city='Casino City',
            state='Casino State',
            country='Malta',
            postal_code='54321',
            status='pending',
            created_by=self.user
        )
    
    def test_analyze_transaction_patterns(self):
        """Test the transaction pattern analysis function"""
        # Analyze retail merchant
        retail_analysis = analyze_transaction_patterns(self.retail_merchant)
        
        self.assertIsNotNone(retail_analysis)
        self.assertTrue('average_transaction_amount' in retail_analysis)
        self.assertTrue('monthly_transaction_volume' in retail_analysis)
        self.assertTrue('high_risk_countries_percentage' in retail_analysis)
        self.assertTrue('unusual_hours_percentage' in retail_analysis)
        self.assertTrue('similar_transactions_percentage' in retail_analysis)
        self.assertTrue('chargeback_rate' in retail_analysis)
        self.assertTrue('detailed_data' in retail_analysis)
        
        # Analyze gambling merchant
        gambling_analysis = analyze_transaction_patterns(self.gambling_merchant)
        
        self.assertIsNotNone(gambling_analysis)
        
        # Gambling merchant should have higher risk metrics
        self.assertGreater(
            gambling_analysis['high_risk_countries_percentage'],
            retail_analysis['high_risk_countries_percentage']
        )
        self.assertGreater(
            gambling_analysis['unusual_hours_percentage'],
            retail_analysis['unusual_hours_percentage']
        )
        self.assertGreater(
            gambling_analysis['chargeback_rate'],
            retail_analysis['chargeback_rate']
        )
    
    def test_generate_simulated_transactions(self):
        """Test the transaction simulation function"""
        # Generate transactions for retail merchant
        retail_transactions = generate_simulated_transactions(self.retail_merchant)
        
        self.assertIsNotNone(retail_transactions)
        self.assertGreater(len(retail_transactions), 0)
        
        # Check transaction structure
        sample_transaction = retail_transactions[0]
        self.assertTrue('timestamp' in sample_transaction)
        self.assertTrue('amount' in sample_transaction)
        self.assertTrue('country' in sample_transaction)
        self.assertTrue('is_chargeback' in sample_transaction)
        self.assertTrue('transaction_id' in sample_transaction)
        
        # Generate transactions for gambling merchant
        gambling_transactions = generate_simulated_transactions(self.gambling_merchant)
        
        self.assertIsNotNone(gambling_transactions)
        self.assertGreater(len(gambling_transactions), 0)
        
        # Gambling should have more transactions than retail
        self.assertGreater(len(gambling_transactions), len(retail_transactions))
        
        # Count chargebacks in both
        retail_chargebacks = sum(1 for t in retail_transactions if t['is_chargeback'])
        gambling_chargebacks = sum(1 for t in gambling_transactions if t['is_chargeback'])
        
        # Calculate chargeback rates
        retail_cb_rate = retail_chargebacks / len(retail_transactions) if retail_transactions else 0
        gambling_cb_rate = gambling_chargebacks / len(gambling_transactions) if gambling_transactions else 0
        
        # Gambling should have higher chargeback rate
        self.assertGreater(gambling_cb_rate, retail_cb_rate)
    
    def test_cluster_transaction_amounts(self):
        """Test the transaction amount clustering function"""
        # Test with regular distribution
        amounts = [10.0, 12.0, 15.0, 50.0, 52.0, 55.0, 100.0, 105.0, 110.0]
        clusters = cluster_transaction_amounts(amounts)
        
        self.assertIsNotNone(clusters)
        self.assertGreater(len(clusters), 0)
        
        # Test with empty list
        empty_clusters = cluster_transaction_amounts([])
        self.assertEqual(empty_clusters, {})
        
        # Test with single value
        single_cluster = cluster_transaction_amounts([42.0])
        self.assertEqual(len(single_cluster), 1)
        
        # Test with similar values (should create fewer clusters)
        similar_amounts = [100.0, 101.0, 100.5, 99.5, 100.2, 98.7, 101.3]
        similar_clusters = cluster_transaction_amounts(similar_amounts)
        self.assertLessEqual(len(similar_clusters), 2)
