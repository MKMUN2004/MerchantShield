"""
Transaction pattern analysis module for merchant verification.
This module analyzes transaction patterns to identify potential risks.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
import random
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of high-risk countries for transaction analysis
HIGH_RISK_COUNTRIES = [
    'afghanistan', 'belarus', 'burma', 'burundi', 'central african republic',
    'cuba', 'democratic republic of the congo', 'iran', 'iraq', 'libya',
    'mali', 'nicaragua', 'north korea', 'somalia', 'south sudan', 'sudan',
    'syria', 'venezuela', 'yemen', 'zimbabwe'
]


def analyze_transaction_patterns(merchant):
    """
    Analyze transaction patterns for a merchant to detect potential risk signals.
    
    In a production environment, this function would retrieve actual transaction data
    from a payment processing system. For this demo, we'll simulate transaction data
    based on merchant attributes.
    
    Args:
        merchant (Merchant): The merchant object to analyze
        
    Returns:
        dict: Analysis results with risk indicators
    """
    logger.info(f"Analyzing transaction patterns for merchant: {merchant.name}")
    
    # In a real system, we would retrieve actual transaction data
    # For this demo, we'll simulate transaction data based on merchant attributes
    transactions = generate_simulated_transactions(merchant)
    
    if not transactions:
        logger.warning(f"No transaction data available for {merchant.name}")
        return {
            'average_transaction_amount': None,
            'monthly_transaction_volume': 0,
            'high_risk_countries_percentage': 0,
            'unusual_hours_percentage': 0,
            'similar_transactions_percentage': 0,
            'chargeback_rate': 0,
            'detailed_data': None
        }
    
    # Calculate key metrics
    try:
        # 1. Basic statistics
        transaction_amounts = [t['amount'] for t in transactions]
        average_amount = sum(transaction_amounts) / len(transaction_amounts)
        transaction_volume = len(transactions)
        
        # 2. Geographic distribution
        countries = [t['country'] for t in transactions]
        high_risk_countries_count = sum(1 for c in countries if c.lower() in HIGH_RISK_COUNTRIES)
        high_risk_countries_percentage = (high_risk_countries_count / len(countries)) * 100 if countries else 0
        
        # 3. Time distribution
        transaction_hours = [t['timestamp'].hour for t in transactions]
        unusual_hours = sum(1 for h in transaction_hours if h >= 22 or h <= 5)
        unusual_hours_percentage = (unusual_hours / len(transaction_hours)) * 100 if transaction_hours else 0
        
        # 4. Transaction similarity analysis
        # In a real system, this would be more sophisticated
        amount_clusters = cluster_transaction_amounts(transaction_amounts)
        largest_cluster_size = max(amount_clusters.values())
        similar_transactions_percentage = (largest_cluster_size / len(transaction_amounts)) * 100
        
        # 5. Chargeback rate
        chargebacks = sum(1 for t in transactions if t.get('is_chargeback', False))
        chargeback_rate = (chargebacks / len(transactions)) * 100
        
        # Prepare country distribution for visualization
        country_distribution = {}
        for country in countries:
            country_distribution[country] = country_distribution.get(country, 0) + 1
        
        # Prepare hourly distribution for visualization
        hourly_distribution = {}
        for hour in transaction_hours:
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        # Store detailed data for reporting
        detailed_data = {
            'country_distribution': country_distribution,
            'hourly_distribution': hourly_distribution,
            'amount_distribution': amount_clusters,
            'transaction_count': transaction_volume,
            'chargeback_count': chargebacks
        }
        
        # Prepare the analysis result
        result = {
            'average_transaction_amount': average_amount,
            'monthly_transaction_volume': transaction_volume,
            'high_risk_countries_percentage': high_risk_countries_percentage,
            'unusual_hours_percentage': unusual_hours_percentage,
            'similar_transactions_percentage': similar_transactions_percentage,
            'chargeback_rate': chargeback_rate,
            'detailed_data': detailed_data
        }
        
        logger.info(f"Transaction analysis completed for {merchant.name}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing transactions: {str(e)}")
        return {
            'average_transaction_amount': None,
            'monthly_transaction_volume': 0,
            'high_risk_countries_percentage': 0,
            'unusual_hours_percentage': 0,
            'similar_transactions_percentage': 0,
            'chargeback_rate': 0,
            'detailed_data': None,
            'error': str(e)
        }


def generate_simulated_transactions(merchant):
    """
    Generate simulated transaction data for demonstration purposes.
    In a real system, this would be replaced with actual transaction data.
    
    The simulation logic creates more suspicious patterns for merchants with:
    - Gambling business type
    - High risk countries
    - Incomplete information
    
    Args:
        merchant (Merchant): The merchant to generate transactions for
        
    Returns:
        list: A list of simulated transactions
    """
    # Determine characteristics based on merchant attributes
    is_high_risk = merchant.business_type == 'gambling' or (merchant.country and merchant.country.lower() in HIGH_RISK_COUNTRIES)
    is_financial = merchant.business_type == 'financial'
    is_online = merchant.business_type == 'online'
    
    # Number of transactions to generate
    if is_high_risk:
        transaction_count = random.randint(500, 2000)
    elif is_financial or is_online:
        transaction_count = random.randint(200, 1000)
    else:
        transaction_count = random.randint(50, 500)
    
    # Transaction amount ranges based on business type
    if merchant.business_type == 'retail':
        amount_min, amount_max = 10, 500
    elif merchant.business_type == 'financial':
        amount_min, amount_max = 100, 5000
    elif merchant.business_type == 'gambling':
        amount_min, amount_max = 20, 1000
    else:
        amount_min, amount_max = 50, 1000
    
    # Countries to distribute transactions across
    if is_high_risk:
        # Higher percentage of high-risk countries
        high_risk_percentage = random.uniform(0.2, 0.6)
    else:
        # Lower percentage of high-risk countries
        high_risk_percentage = random.uniform(0, 0.1)
    
    # Common countries for transactions
    common_countries = ['United States', 'United Kingdom', 'Canada', 'Germany', 'France', 
                       'Australia', 'Japan', 'Italy', 'Spain', 'Netherlands']
    
    # Generate transactions
    now = datetime.now()
    transactions = []
    
    for i in range(transaction_count):
        # Determine transaction date (within last 30 days)
        days_ago = random.randint(0, 30)
        transaction_date = now - timedelta(days=days_ago)
        
        # Determine if this transaction is from a high-risk country
        is_high_risk_country = random.random() < high_risk_percentage
        
        if is_high_risk_country:
            country = random.choice(HIGH_RISK_COUNTRIES).title()
        else:
            country = random.choice(common_countries)
        
        # For high-risk merchants, create more unusual patterns
        if is_high_risk:
            # More late-night transactions
            hour = random.choices(
                range(24), 
                weights=[1, 1, 1, 1, 1, 1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 3, 3, 2, 2], 
                k=1
            )[0]
            
            # Higher chargeback probability
            is_chargeback = random.random() < 0.03
            
            # More similar transaction amounts
            if random.random() < 0.7:
                # Cluster transactions around certain values
                amount = round(random.choice([25, 50, 100, 200, 500]), 2)
            else:
                amount = round(random.uniform(amount_min, amount_max), 2)
        else:
            # Normal distribution of transaction times
            hour = random.choices(
                range(24), 
                weights=[1, 1, 1, 1, 1, 1, 2, 4, 6, 8, 8, 8, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1], 
                k=1
            )[0]
            
            # Normal chargeback rate
            is_chargeback = random.random() < 0.01
            
            # More varied transaction amounts
            amount = round(random.uniform(amount_min, amount_max), 2)
        
        # Create the transaction timestamp
        transaction_timestamp = transaction_date.replace(hour=hour, minute=random.randint(0, 59))
        
        transaction = {
            'timestamp': transaction_timestamp,
            'amount': amount,
            'country': country,
            'is_chargeback': is_chargeback,
            'transaction_id': f"TX{random.randint(10000000, 99999999)}"
        }
        
        transactions.append(transaction)
    
    return transactions


def cluster_transaction_amounts(amounts):
    """
    Cluster transaction amounts to identify patterns of similar transactions.
    
    Args:
        amounts (list): List of transaction amounts
        
    Returns:
        dict: Dictionary with cluster centers and sizes
    """
    if not amounts:
        return {}
    
    # Convert to numpy array and reshape for KMeans
    X = np.array(amounts).reshape(-1, 1)
    
    # Determine optimal number of clusters (simplified method)
    # In a real system, we would use methods like elbow method or silhouette analysis
    k = min(5, len(amounts))
    
    # Perform clustering
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X)
    
    # Count samples in each cluster
    labels = kmeans.labels_
    clusters = {}
    for i in range(k):
        center = round(float(kmeans.cluster_centers_[i][0]), 2)
        count = np.sum(labels == i)
        clusters[center] = int(count)
    
    return clusters
