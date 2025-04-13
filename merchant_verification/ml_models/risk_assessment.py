"""
Risk assessment machine learning model for merchant verification.
This module provides the functionality to assess the risk of merchants
using various attributes and criteria.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import pandas as pd
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of high-risk countries
HIGH_RISK_COUNTRIES = [
    'afghanistan', 'belarus', 'burma', 'burundi', 'central african republic',
    'cuba', 'democratic republic of the congo', 'iran', 'iraq', 'libya',
    'mali', 'nicaragua', 'north korea', 'somalia', 'south sudan', 'sudan',
    'syria', 'venezuela', 'yemen', 'zimbabwe'
]

# List of gambling-related keywords
GAMBLING_KEYWORDS = [
    'bet', 'betting', 'casino', 'gambling', 'poker', 'slot', 'slots', 'lottery',
    'wager', 'wagering', 'bingo', 'roulette', 'blackjack', 'sportsbook',
    'bookmaker', 'bookmaking'
]

# Business type risk scores
BUSINESS_TYPE_RISK = {
    'retail': 1.0,
    'online': 2.0,
    'service': 1.5,
    'financial': 3.0,
    'gambling': 5.0,
    'travel': 2.0,
    'healthcare': 1.5,
    'other': 2.5
}


def assess_merchant_risk(merchant):
    """
    Assess the risk level of a merchant using various factors.
    
    Args:
        merchant (Merchant): A merchant object with attributes for assessment
        
    Returns:
        dict: Risk assessment data including risk score and level
    """
    logger.info(f"Assessing risk for merchant: {merchant.name}")
    
    # Initialize risk factors
    risk_factors = {}
    
    # 1. Business type risk
    business_type_score = BUSINESS_TYPE_RISK.get(merchant.business_type, 2.5)
    risk_factors['business_type_risk'] = business_type_score
    
    # 2. Country risk
    country_risk = 1.0
    if merchant.country and merchant.country.lower() in HIGH_RISK_COUNTRIES:
        country_risk = 5.0
    risk_factors['country_risk'] = country_risk
    
    # 3. Website content analysis (if website exists)
    website_risk = analyze_website_risk(merchant.website)
    risk_factors['website_risk'] = website_risk
    
    # 4. Registration information completeness
    completeness_risk = assess_information_completeness(merchant)
    risk_factors['completeness_risk'] = completeness_risk
    
    # 5. Business age risk
    # For demo purposes, assume all are new businesses with higher risk
    business_age_risk = 3.0
    risk_factors['business_age_risk'] = business_age_risk
    
    # 6. Transaction pattern risk (if available)
    if hasattr(merchant, 'transaction_patterns') and merchant.transaction_patterns.exists():
        try:
            transaction_pattern = merchant.transaction_patterns.latest('analysis_date')
            transaction_risk = assess_transaction_risk(transaction_pattern)
            risk_factors['transaction_risk'] = transaction_risk
        except Exception as e:
            logger.error(f"Error assessing transaction risk: {str(e)}")
            risk_factors['transaction_risk'] = 2.5
    else:
        # No transaction data available
        risk_factors['transaction_risk'] = 2.5
    
    # Calculate the overall risk score (weighted average)
    weights = {
        'business_type_risk': 0.25,
        'country_risk': 0.20,
        'website_risk': 0.20,
        'completeness_risk': 0.15,
        'business_age_risk': 0.10,
        'transaction_risk': 0.10
    }
    
    risk_score = sum(risk_factors[factor] * weights[factor] for factor in risk_factors)
    
    # Determine risk level based on score
    risk_level = determine_risk_level(risk_score)
    
    # Generate risk assessment details
    risk_assessment = {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'suggested_risk_level': risk_level,
        'risk_factors': risk_factors,
        'high_risk_flags': identify_high_risk_flags(risk_factors, merchant),
        'recommendations': generate_recommendations(risk_level, risk_factors, merchant)
    }
    
    logger.info(f"Risk assessment completed for {merchant.name}. Score: {risk_score}, Level: {risk_level}")
    
    return risk_assessment


def analyze_website_risk(website_url):
    """
    Analyze a merchant's website for risk factors.
    In a production system, this would connect to external content analysis services.
    
    Args:
        website_url (str): URL of the merchant website
        
    Returns:
        float: Website risk score between 1.0 (low risk) and 5.0 (high risk)
    """
    if not website_url:
        # No website provided, moderate risk
        return 3.0
    
    # Simple check for gambling keywords in the URL
    # In a real system, this would involve web scraping and content analysis
    website_lower = website_url.lower()
    
    gambling_risk = any(keyword in website_lower for keyword in GAMBLING_KEYWORDS)
    if gambling_risk:
        return 5.0
    
    # Check for suspicious TLDs
    suspicious_tlds = ['.bet', '.casino', '.poker', '.game']
    if any(website_lower.endswith(tld) for tld in suspicious_tlds):
        return 4.5
    
    # For unknown websites, assign a moderate risk by default
    return 2.0


def assess_information_completeness(merchant):
    """
    Assess the completeness and validity of merchant information.
    
    Args:
        merchant (Merchant): Merchant object with attributes
        
    Returns:
        float: Risk score based on information completeness
    """
    # Required fields for a complete merchant profile
    required_fields = [
        'name', 'business_type', 'registration_number', 
        'email', 'phone', 'address', 'city', 'state', 'country'
    ]
    
    # Count filled required fields
    filled_fields = sum(1 for field in required_fields if getattr(merchant, field))
    completeness_ratio = filled_fields / len(required_fields)
    
    # Convert to risk score (lower completeness = higher risk)
    completeness_risk = 5.0 - (completeness_ratio * 4.0)
    
    return max(1.0, completeness_risk)


def assess_transaction_risk(transaction_pattern):
    """
    Assess risk based on transaction patterns.
    
    Args:
        transaction_pattern (TransactionPattern): Transaction pattern data
        
    Returns:
        float: Risk score for transaction patterns
    """
    risk_score = 1.0
    
    # High volume of transactions might indicate higher risk
    if transaction_pattern.monthly_transaction_volume:
        if transaction_pattern.monthly_transaction_volume > 10000:
            risk_score += 1.5
        elif transaction_pattern.monthly_transaction_volume > 5000:
            risk_score += 1.0
        elif transaction_pattern.monthly_transaction_volume > 1000:
            risk_score += 0.5
    
    # High percentage of transactions from high-risk countries
    if transaction_pattern.high_risk_countries_percentage:
        if transaction_pattern.high_risk_countries_percentage > 50:
            risk_score += 2.0
        elif transaction_pattern.high_risk_countries_percentage > 25:
            risk_score += 1.5
        elif transaction_pattern.high_risk_countries_percentage > 10:
            risk_score += 1.0
    
    # High chargeback rate indicates risk
    if transaction_pattern.chargeback_rate:
        if transaction_pattern.chargeback_rate > 2.0:
            risk_score += 2.0
        elif transaction_pattern.chargeback_rate > 1.0:
            risk_score += 1.0
        elif transaction_pattern.chargeback_rate > 0.5:
            risk_score += 0.5
    
    # Unusual hours transactions
    if transaction_pattern.unusual_hours_percentage:
        if transaction_pattern.unusual_hours_percentage > 30:
            risk_score += 1.0
        elif transaction_pattern.unusual_hours_percentage > 15:
            risk_score += 0.5
    
    # Similar/repeated transactions
    if transaction_pattern.similar_transactions_percentage:
        if transaction_pattern.similar_transactions_percentage > 70:
            risk_score += 1.0
        elif transaction_pattern.similar_transactions_percentage > 50:
            risk_score += 0.5
    
    return min(5.0, risk_score)  # Cap at 5.0


def determine_risk_level(risk_score):
    """
    Determine risk level category based on numerical score.
    
    Args:
        risk_score (float): Numerical risk score
        
    Returns:
        str: Risk level category
    """
    if risk_score >= 4.0:
        return 'extreme'
    elif risk_score >= 3.0:
        return 'high'
    elif risk_score >= 2.0:
        return 'medium'
    else:
        return 'low'


def identify_high_risk_flags(risk_factors, merchant):
    """
    Identify specific high-risk flags for a merchant.
    
    Args:
        risk_factors (dict): Risk factor scores
        merchant (Merchant): Merchant object
        
    Returns:
        list: List of specific risk flags
    """
    flags = []
    
    # Check business type
    if merchant.business_type == 'gambling':
        flags.append("Gambling/gaming business type")
    
    # Check country
    if merchant.country and merchant.country.lower() in HIGH_RISK_COUNTRIES:
        flags.append(f"Located in high-risk country: {merchant.country}")
    
    # Check website
    if risk_factors.get('website_risk', 0) >= 4.0:
        flags.append("Website contains gambling-related content")
    
    # Check information completeness
    if risk_factors.get('completeness_risk', 0) >= 3.5:
        flags.append("Incomplete merchant information")
    
    # Check transaction patterns
    if risk_factors.get('transaction_risk', 0) >= 3.5:
        flags.append("Suspicious transaction patterns")
        
        # Get more specific transaction flags
        if hasattr(merchant, 'transaction_patterns') and merchant.transaction_patterns.exists():
            tp = merchant.transaction_patterns.latest('analysis_date')
            
            if tp.high_risk_countries_percentage and tp.high_risk_countries_percentage > 25:
                flags.append(f"High percentage ({tp.high_risk_countries_percentage}%) of transactions from high-risk countries")
                
            if tp.chargeback_rate and tp.chargeback_rate > 1.0:
                flags.append(f"Elevated chargeback rate: {tp.chargeback_rate}%")
    
    return flags


def generate_recommendations(risk_level, risk_factors, merchant):
    """
    Generate recommendations based on risk assessment.
    
    Args:
        risk_level (str): Risk level category
        risk_factors (dict): Risk factor scores
        merchant (Merchant): Merchant object
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    if risk_level in ['high', 'extreme']:
        recommendations.append("Conduct enhanced due diligence (EDD)")
        recommendations.append("Verify business registration with official sources")
        recommendations.append("Request additional documentation for business legitimacy")
        
        if merchant.business_type in ['gambling', 'financial']:
            recommendations.append("Verify appropriate licenses for regulated business activities")
        
        if risk_factors.get('website_risk', 0) >= 3.5:
            recommendations.append("Conduct detailed content analysis of merchant website")
            
        if merchant.country and merchant.country.lower() in HIGH_RISK_COUNTRIES:
            recommendations.append(f"Implement additional monitoring for transactions from {merchant.country}")
    
    elif risk_level == 'medium':
        recommendations.append("Verify business registration documentation")
        recommendations.append("Monitor transaction patterns during initial period")
        
        if risk_factors.get('completeness_risk', 0) >= 3.0:
            recommendations.append("Request complete merchant information")
    
    else:  # low risk
        recommendations.append("Standard verification procedures")
        recommendations.append("Periodic review of transaction patterns")
    
    return recommendations
