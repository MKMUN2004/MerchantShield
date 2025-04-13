"""
ASGI config for Enhanced Merchant Verification System.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emvs.settings')

application = get_asgi_application()
