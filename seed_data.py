import os
import django
import random
from datetime import datetime, timedelta

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emvs.settings')
django.setup()

# Import models
from django.contrib.auth.models import User
from merchant_verification.models import (
    Merchant,
    TransactionPattern,
    VerificationFlag,
    VerificationReport,
    AuditLog
)

def seed_database():
    """Seed the database with sample data for testing and demonstration"""
    print("Seeding database with sample data...")
    
    # Get admin user or create if doesn't exist
    try:
        admin_user = User.objects.get(username='admin')
        print("Using existing admin user")
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("Created admin user")
    
    # Create sample merchants
    merchants_data = [
        {
            'name': 'Retail Express',
            'business_type': 'retail',
            'registration_number': 'REG123456',
            'tax_id': 'TAX123456',
            'website': 'https://www.retailexpress.com',
            'email': 'info@retailexpress.com',
            'phone': '+12025550147',
            'address': '123 Retail Street',
            'city': 'New York',
            'state': 'NY',
            'country': 'United States',
            'postal_code': '10001',
            'status': 'verified',
            'risk_level': 'low',
            'risk_score': 1.2
        },
        {
            'name': 'E-Shop Central',
            'business_type': 'online',
            'registration_number': 'REG654321',
            'tax_id': 'TAX654321',
            'website': 'https://www.eshopcentral.com',
            'email': 'info@eshopcentral.com',
            'phone': '+12025550158',
            'address': '456 E-commerce Avenue',
            'city': 'San Francisco',
            'state': 'CA',
            'country': 'United States',
            'postal_code': '94105',
            'status': 'verified',
            'risk_level': 'medium',
            'risk_score': 2.5
        },
        {
            'name': 'Financial Services Inc.',
            'business_type': 'financial',
            'registration_number': 'REG789012',
            'tax_id': 'TAX789012',
            'website': 'https://www.finservices.com',
            'email': 'info@finservices.com',
            'phone': '+12025550169',
            'address': '789 Finance Way',
            'city': 'Chicago',
            'state': 'IL',
            'country': 'United States',
            'postal_code': '60601',
            'status': 'verified',
            'risk_level': 'medium',
            'risk_score': 2.8
        },
        {
            'name': 'Lucky Bets Casino',
            'business_type': 'gambling',
            'registration_number': 'REG345678',
            'tax_id': 'TAX345678',
            'website': 'https://www.luckybetscasino.com',
            'email': 'info@luckybetscasino.com',
            'phone': '+35627893456',
            'address': '10 Casino Street',
            'city': 'Valletta',
            'state': '',
            'country': 'Malta',
            'postal_code': 'VLT 1117',
            'status': 'flagged',
            'risk_level': 'high',
            'risk_score': 3.7
        },
        {
            'name': 'Global Travel Agency',
            'business_type': 'travel',
            'registration_number': 'REG901234',
            'tax_id': 'TAX901234',
            'website': 'https://www.globaltravelagency.com',
            'email': 'info@globaltravelagency.com',
            'phone': '+12025550184',
            'address': '567 Tourism Road',
            'city': 'Miami',
            'state': 'FL',
            'country': 'United States',
            'postal_code': '33122',
            'status': 'pending',
            'risk_level': None,
            'risk_score': None
        },
        {
            'name': 'Healthcare Solutions',
            'business_type': 'healthcare',
            'registration_number': 'REG567890',
            'tax_id': 'TAX567890',
            'website': 'https://www.healthcaresolutions.com',
            'email': 'info@healthcaresolutions.com',
            'phone': '+12025550195',
            'address': '890 Health Drive',
            'city': 'Boston',
            'state': 'MA',
            'country': 'United States',
            'postal_code': '02110',
            'status': 'pending',
            'risk_level': None,
            'risk_score': None
        },
        {
            'name': 'Tech Services LLC',
            'business_type': 'service',
            'registration_number': 'REG234567',
            'tax_id': 'TAX234567',
            'website': 'https://www.techservicesllc.com',
            'email': 'info@techservicesllc.com',
            'phone': '+12025550176',
            'address': '432 Tech Street',
            'city': 'Seattle',
            'state': 'WA',
            'country': 'United States',
            'postal_code': '98101',
            'status': 'verified',
            'risk_level': 'low',
            'risk_score': 1.5
        },
        {
            'name': 'Luxury Goods Import',
            'business_type': 'retail',
            'registration_number': 'REG432156',
            'tax_id': 'TAX432156',
            'website': 'https://www.luxurygoodsimport.com',
            'email': 'info@luxurygoodsimport.com',
            'phone': '+41789012345',
            'address': '15 Luxury Avenue',
            'city': 'Geneva',
            'state': '',
            'country': 'Switzerland',
            'postal_code': '1207',
            'status': 'verified',
            'risk_level': 'low',
            'risk_score': 1.8
        },
        {
            'name': 'Digital Gaming Platform',
            'business_type': 'online',
            'registration_number': 'REG876543',
            'tax_id': '',  # Missing tax ID
            'website': 'https://www.digitalgames.bet',
            'email': 'info@digitalgames.bet',
            'phone': '+35627891234',
            'address': '20 Gaming Street',
            'city': 'Valletta',
            'state': '',
            'country': 'Malta',
            'postal_code': 'VLT 1118',
            'status': 'flagged',
            'risk_level': 'high',
            'risk_score': 3.9
        },
        {
            'name': 'Incomplete Business',
            'business_type': 'other',
            'registration_number': 'REG999999',
            'tax_id': '',  # Missing tax ID
            'website': '',  # Missing website
            'email': 'incomplete@example.com',
            'phone': '+12025550999',
            'address': '',  # Missing address
            'city': 'Unknown',
            'state': '',
            'country': 'United States',
            'postal_code': '',  # Missing postal code
            'status': 'rejected',
            'risk_level': 'extreme',
            'risk_score': 4.5
        }
    ]
    
    # Create merchants
    merchants = []
    for merchant_data in merchants_data:
        # Check if merchant already exists
        existing_merchant = Merchant.objects.filter(
            registration_number=merchant_data['registration_number']
        ).first()
        
        if existing_merchant:
            print(f"Merchant {merchant_data['name']} already exists, skipping...")
            merchants.append(existing_merchant)
            continue
        
        # Create new merchant
        merchant = Merchant.objects.create(
            name=merchant_data['name'],
            business_type=merchant_data['business_type'],
            registration_number=merchant_data['registration_number'],
            tax_id=merchant_data['tax_id'],
            website=merchant_data['website'],
            email=merchant_data['email'],
            phone=merchant_data['phone'],
            address=merchant_data['address'],
            city=merchant_data['city'],
            state=merchant_data['state'],
            country=merchant_data['country'],
            postal_code=merchant_data['postal_code'],
            status=merchant_data['status'],
            risk_level=merchant_data['risk_level'],
            risk_score=merchant_data['risk_score'],
            created_by=admin_user,
            verified_by=admin_user if merchant_data['status'] == 'verified' else None,
            last_verified_at=datetime.now() if merchant_data['status'] == 'verified' else None
        )
        
        merchants.append(merchant)
        print(f"Created merchant: {merchant.name}")
    
    # Create transaction patterns for each merchant
    for merchant in merchants:
        # Skip if transaction pattern already exists
        if TransactionPattern.objects.filter(merchant=merchant).exists():
            print(f"Transaction pattern for {merchant.name} already exists, skipping...")
            continue
        
        # Higher risk for gambling and unknown business types
        high_risk = merchant.business_type in ['gambling'] or merchant.status == 'flagged'
        missing_info = merchant.status == 'rejected'
        
        pattern = TransactionPattern.objects.create(
            merchant=merchant,
            average_transaction_amount=random.uniform(50, 500),
            monthly_transaction_volume=random.randint(100, 5000),
            high_risk_countries_percentage=random.uniform(30, 75) if high_risk else random.uniform(1, 10),
            unusual_hours_percentage=random.uniform(20, 60) if high_risk else random.uniform(5, 15),
            similar_transactions_percentage=random.uniform(50, 90) if high_risk else random.uniform(10, 30),
            chargeback_rate=random.uniform(2, 5) if high_risk else random.uniform(0.1, 1),
            transaction_data={
                'country_distribution': {
                    'United States': random.randint(100, 1000),
                    'United Kingdom': random.randint(50, 500),
                    'Canada': random.randint(25, 250),
                    'Germany': random.randint(25, 250),
                    'France': random.randint(25, 250),
                    'China': random.randint(10, 100),
                    'Russia': random.randint(5, 50) if high_risk else random.randint(1, 10),
                    'Iran': random.randint(5, 50) if high_risk else 0,
                    'North Korea': random.randint(1, 10) if high_risk else 0
                },
                'hourly_distribution': {
                    '8': random.randint(10, 50),
                    '9': random.randint(20, 100),
                    '10': random.randint(30, 150),
                    '11': random.randint(40, 200),
                    '12': random.randint(50, 250),
                    '13': random.randint(40, 200),
                    '14': random.randint(30, 150),
                    '15': random.randint(20, 100),
                    '16': random.randint(10, 50),
                    '17': random.randint(5, 25),
                    '22': random.randint(20, 100) if high_risk else random.randint(1, 5),
                    '23': random.randint(15, 75) if high_risk else random.randint(1, 5),
                    '0': random.randint(10, 50) if high_risk else random.randint(1, 5),
                    '1': random.randint(5, 25) if high_risk else random.randint(1, 5),
                    '2': random.randint(5, 25) if high_risk else 0,
                    '3': random.randint(5, 25) if high_risk else 0
                }
            }
        )
        
        print(f"Created transaction pattern for {merchant.name}")
    
    # Create flags for flagged merchants
    flag_types = {
        'gambling': [
            {
                'flag_type': 'suspicious_website',
                'description': 'Website contains gambling content possibly targeting restricted regions.',
                'severity': 'high'
            },
            {
                'flag_type': 'high_risk_location',
                'description': 'Business is registered in a high-risk jurisdiction known for lax gambling regulations.',
                'severity': 'medium'
            },
            {
                'flag_type': 'transaction_pattern',
                'description': 'Unusual transaction patterns observed with high rates of chargebacks.',
                'severity': 'high'
            }
        ],
        'missing_info': [
            {
                'flag_type': 'missing_info',
                'description': 'Critical business information is missing or incomplete.',
                'severity': 'medium'
            },
            {
                'flag_type': 'external_data',
                'description': 'Unable to verify business existence through external data sources.',
                'severity': 'high'
            },
            {
                'flag_type': 'regulatory',
                'description': 'No evidence of regulatory compliance for the stated business type.',
                'severity': 'critical'
            }
        ]
    }
    
    for merchant in merchants:
        if merchant.status in ['flagged', 'rejected']:
            flag_category = 'missing_info' if merchant.business_type == 'other' else 'gambling'
            
            # Skip if flags already exist
            if VerificationFlag.objects.filter(merchant=merchant).exists():
                print(f"Flags for {merchant.name} already exist, skipping...")
                continue
            
            for flag_data in flag_types[flag_category]:
                flag = VerificationFlag.objects.create(
                    merchant=merchant,
                    flag_type=flag_data['flag_type'],
                    description=flag_data['description'],
                    severity=flag_data['severity'],
                    created_by=admin_user
                )
                
                print(f"Created flag: {flag.flag_type} for {merchant.name}")
    
    # Create verification reports for verified merchants
    for merchant in merchants:
        if merchant.status == 'verified':
            # Skip if report already exists
            if VerificationReport.objects.filter(merchant=merchant).exists():
                print(f"Report for {merchant.name} already exists, skipping...")
                continue
            
            report = VerificationReport.objects.create(
                merchant=merchant,
                generated_by=admin_user,
                report_data={
                    'merchant_info': {
                        'name': merchant.name,
                        'business_type': merchant.business_type,
                        'registration_number': merchant.registration_number,
                        'status': merchant.status,
                        'risk_level': merchant.risk_level,
                        'risk_score': merchant.risk_score,
                    },
                    'verification_details': {
                        'document_verification': True,
                        'website_analysis': True,
                        'business_registration_verified': True,
                        'contact_verification': True,
                        'ownership_verification': True
                    },
                    'external_api_data': {
                        'business_exists': True,
                        'registration_matches': True,
                        'high_risk_database_check': False,
                        'sanctions_check': False
                    },
                    'transaction_pattern': {
                        'average_transaction_amount': str(merchant.transaction_patterns.first().average_transaction_amount),
                        'monthly_transaction_volume': merchant.transaction_patterns.first().monthly_transaction_volume,
                        'high_risk_countries_percentage': merchant.transaction_patterns.first().high_risk_countries_percentage,
                        'chargeback_rate': merchant.transaction_patterns.first().chargeback_rate,
                    },
                    'flags': []
                },
                risk_assessment=f"Merchant is {merchant.risk_level} risk based on business type and transaction patterns.",
                recommendations="Standard verification procedures. Periodic review of transaction patterns."
            )
            
            print(f"Created verification report for {merchant.name}")
    
    # Create audit logs
    for merchant in merchants:
        # Create some audit logs
        AuditLog.objects.create(
            user=admin_user,
            merchant=merchant,
            action='create',
            ip_address='127.0.0.1',
            details={
                'fields_updated': ['name', 'registration_number', 'email']
            }
        )
        
        if merchant.status in ['verified', 'flagged', 'rejected']:
            AuditLog.objects.create(
                user=admin_user,
                merchant=merchant,
                action='verify' if merchant.status == 'verified' else 'flag' if merchant.status == 'flagged' else 'reject',
                ip_address='127.0.0.1',
                details={
                    'previous_status': 'pending',
                    'new_status': merchant.status,
                    'risk_level': merchant.risk_level,
                    'risk_score': merchant.risk_score
                }
            )
        
        print(f"Created audit logs for {merchant.name}")
    
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()