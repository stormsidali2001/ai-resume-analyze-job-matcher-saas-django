"""
config/settings/local.py

Development overrides.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Surface real tracebacks in tests instead of 500 responses
DEBUG_PROPAGATE_EXCEPTIONS = True
