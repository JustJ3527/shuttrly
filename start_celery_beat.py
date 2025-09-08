#!/usr/bin/env python
"""
Script to start Celery Beat for periodic recommendation updates.
Run this alongside your main Django application.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuttrly.settings')
django.setup()

from celery import Celery
from shuttrly.celery import app

if __name__ == '__main__':
    # Start Celery Beat
    print("🚀 Starting Celery Beat for periodic recommendation updates...")
    print("📅 Schedule:")
    print("   - Update recommendations: Every 30 minutes")
    print("   - Cleanup old recommendations: Every hour")
    print("   - Press Ctrl+C to stop")
    
    app.start(['beat', '--loglevel=info'])
