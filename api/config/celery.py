"""
config/celery.py

Celery application for background task processing.

Start a worker with:
    celery -A config worker --loglevel=info
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("resumeai")

# Pull all CELERY_* settings from Django's settings module
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all INSTALLED_APPS
app.autodiscover_tasks()
