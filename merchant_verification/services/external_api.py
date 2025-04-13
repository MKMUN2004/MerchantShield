"""
External API integration service for merchant verification.
This module handles integration with external data sources to verify merchant information.
"""

import requests
import json
import os
import logging
from datetime import datetime
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from environment variables
API_KEY = os.getenv('EXTERNAL_API_KEY', '')
API_BASE_URL = os.getenv('BUSINESS_VERIFICATION_API_URL', 'https://api.example.com/business-verification/')


def verify_merchant_external(merchant):
    """
    Verify merchant information with external business verification service.
    
    In a production environment, this would make real API calls to verification services.
    For this demo, we simulate API responses based on merchant attributes.
    
    Args:
        merchant (Merchant): The merchant to verify
        
    Returns:
        dict: Verification data from external sources
    """
    logger.info(f"Verifying merchant {merchant.name} with external APIs")
    
    try:
        # In a real system, we would call actual external APIs
        # For this demo, simulate API responses based on merchant attributes
        
        # Simulate an API call with delay (commented out for demo)
        # response = requests.get(
        #     f"{API_BASE_URL}verify",
        #     params={
        #         'business_name': merchant.name,
        #         'registration_number': merchant.registration_number,
        #         'country': merchant.country
        #     },
        #     headers={'Authorization': f'Bearer {API_KEY}'}
        # )
        # verification_data = response.json()
        
        verification_data = simulate_verification_response(merchant)
        
        logger.info(f"External verification completed for {merchant.name}")
        return verification_data
        
    except Exception as e:
        logger.error(f"Error during external verification: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'verification_status': 'error',
            'message': 'Failed to verify with external API'
        }


def simulate_verification_response(merchant):
    """
    Simulate responses from external verification APIs for demonstration.
    
    For realistic simulation, we generate verification responses based on
    merchant attributes like business type, name, and registration number.
    
    Args:
        merchant (Merchant): The merchant to generate responses for
        
    Returns:
        dict: Simulated verification API response
    """
    # Check for missing essential information
    missing_info = not merchant.registration_number or not merchant.name or not merchant.country
    
    # Check for potentially problematic business types
    is_high_risk_business = merchant.business_type in ['gambling', 'financial']
    
    # Check for suspicious patterns in registration number
    suspicious_registration = False
    if merchant.registration_number:
        # Simple pattern check (would be more sophisticated in a real system)
        if len(merchant.registration_number) < 5 or merchant.registration_number.isdigit() or merchant.registration_number.isalpha():
            suspicious_registration = True
    
    # Determine verification outcome based on these factors
    if missing_info:
        verification_status = 'incomplete'
        confidence_score = random.uniform(0.1, 0.4)
        risk_indicators = ['Incomplete business information']
    elif suspicious_registration:
        verification_status = 'suspicious'
        confidence_score = random.uniform(0.2, 0.5)
        risk_indicators = ['Suspicious registration number format']
    elif is_high_risk_business:
        # For high-risk businesses, we sometimes verify, sometimes flag
        if random.random() < 0.7:
            verification_status = 'verified'
            confidence_score = random.uniform(0.6, 0.8)
            risk_indicators = ['High-risk business category']
        else:
            verification_status = 'suspicious'
            confidence_score = random.uniform(0.3, 0.6)
            risk_indicators = ['Potential unlicensed operation in regulated sector']
    else:
        # For normal businesses, mostly verify
        if random.random() < 0.9:
            verification_status = 'verified'
            confidence_score = random.uniform(0.7, 0.95)
            risk_indicators = []
        else:
            verification_status = 'unverified'
            confidence_score = random.uniform(0.4, 0.6)
            risk_indicators = ['Could not confirm business registration']
    
    # For gambling businesses, check for licensing
    if merchant.business_type == 'gambling':
        # Add licensing check
        if verification_status == 'verified':
            has_license = random.random() < 0.7
            if has_license:
                license_info = {
                    'license_number': f"GL-{random.randint(10000, 99999)}",
                    'issuing_authority': random.choice([
                        'Malta Gaming Authority',
                        'UK Gambling Commission',
                        'Gibraltar Regulatory Authority',
                        'Alderney Gambling Control Commission'
                    ]),
                    'valid_until': (datetime.now().replace(
                        year=datetime.now().year + random.randint(1, 3)
                    )).strftime('%Y-%m-%d')
                }
            else:
                verification_status = 'suspicious'
                confidence_score = random.uniform(0.3, 0.5)
                risk_indicators.append('No valid gambling license identified')
                license_info = None
        else:
            license_info = None
    else:
        license_info = None
    
    # Generate business registry information
    if verification_status in ['verified', 'suspicious']:
        registry_info = {
            'registry_name': f"{merchant.country} Business Registry",
            'registration_date': (datetime.now().replace(
                year=datetime.now().year - random.randint(1, 10)
            )).strftime('%Y-%m-%d'),
            'status': 'Active' if verification_status == 'verified' else 'Pending Review',
            'registry_url': f"https://registry.{merchant.country.lower().replace(' ', '')}.example/business"
        }
    else:
        registry_info = None
    
    # Simulate address verification
    address_verified = verification_status == 'verified' and random.random() < 0.9
    
    # Build the full response
    verification_response = {
        'timestamp': datetime.now().isoformat(),
        'request_id': f"req-{random.randint(10000000, 99999999)}",
        'verification_status': verification_status,
        'confidence_score': round(confidence_score, 2),
        'business_details': {
            'name': merchant.name,
            'registration_number': merchant.registration_number,
            'country': merchant.country,
            'address_verified': address_verified,
            'website_domain': merchant.website.split('//')[1].split('/')[0] if merchant.website and '//' in merchant.website else None,
        },
        'registry_information': registry_info,
        'license_information': license_info,
        'risk_indicators': risk_indicators,
        'verification_methods': [
            'Registry Database Check',
            'Business Name Validation',
            'Address Verification',
            'License Database Check' if merchant.business_type == 'gambling' else 'Industry Classification'
        ]
    }
    
    return verification_response


def check_business_sanctions(merchant):
    """
    Check if a business is on any sanctions lists.
    
    In a production environment, this would call real sanctions APIs.
    
    Args:
        merchant (Merchant): The merchant to check
        
    Returns:
        dict: Sanctions check results
    """
    logger.info(f"Checking sanctions for merchant {merchant.name}")
    
    # In a real system, we would call actual sanctions APIs
    # For this demo, we'll simulate responses
    
    # Simulate some merchants being on sanctions lists
    is_sanctioned = merchant.country.lower() in HIGH_RISK_COUNTRIES and random.random() < 0.3
    
    if is_sanctioned:
        sanctions_data = {
            'is_sanctioned': True,
            'lists': [
                {
                    'list_name': 'OFAC SDN',
                    'entry_date': (datetime.now().replace(
                        year=datetime.now().year - random.randint(0, 2)
                    )).strftime('%Y-%m-%d'),
                    'reason': 'Economic sanctions'
                }
            ],
            'match_confidence': random.uniform(0.8, 0.95)
        }
    else:
        sanctions_data = {
            'is_sanctioned': False,
            'lists': [],
            'match_confidence': 0
        }
    
    return sanctions_data


# List of high-risk countries for sanctions checks
HIGH_RISK_COUNTRIES = [
    'afghanistan', 'belarus', 'burma', 'burundi', 'central african republic',
    'cuba', 'democratic republic of the congo', 'iran', 'iraq', 'libya',
    'mali', 'nicaragua', 'north korea', 'somalia', 'south sudan', 'sudan',
    'syria', 'venezuela', 'yemen', 'zimbabwe'
]
