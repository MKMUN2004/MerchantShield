
# Enhanced Merchant Verification System (EMVS)

A Django-based merchant verification system that uses machine learning for risk assessment and transaction pattern analysis.

## Features

- Merchant registration and verification workflow
- ML-based risk assessment and scoring
- Transaction pattern analysis
- Verification flagging system
- Detailed audit logging
- Verification reports generation
- API endpoints for integration

## Tech Stack

- Django 5.2
- Python ML models for risk assessment
- RESTful API with Django REST Framework
- SQLite database
- Bootstrap for frontend

## Getting Started

1. Clone the repository
2. Install dependencies:
```bash
python -m pip install -r requirements.txt
```
3. Run migrations:
```bash
python manage.py migrate
```
4. Load sample data (optional):
```bash
python seed_data.py
```
5. Start the development server:
```bash
python manage.py runserver 0.0.0.0:5000
```

## Project Structure

- `merchant_verification/` - Main application directory
  - `api/` - REST API endpoints
  - `ml_models/` - Machine learning models for risk assessment
  - `services/` - External API integrations
  - `templates/` - HTML templates
  - `static/` - CSS and JavaScript files

## Key Features

### Risk Assessment
- Business type analysis 
- Country risk evaluation
- Transaction pattern analysis
- ML-based scoring system

### Merchant Verification
- Multi-step verification process
- Document verification
- External API integration
- Manual review workflow

### Monitoring
- Transaction pattern monitoring
- Risk level tracking
- Audit logging
- Verification reports

## License

MIT License
