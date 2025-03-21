# src/config/settings.py
"""
Central settings configuration for the Snowfall Alert System.

This module loads environment variables and provides centralized access
to all configuration settings used throughout the application.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file (in development)
load_dotenv()

# API Keys
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
WEATHERAPI_KEY = os.environ.get("WEATHERAPI_KEY", "")

# Slack Integration
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
SLACK_MONITORING_WEBHOOK_URL = os.environ.get("SLACK_MONITORING_WEBHOOK_URL", "")

# Application Settings
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
VERIFICATION_THRESHOLD = float(os.environ.get("VERIFICATION_THRESHOLD", "2.0"))
ALERT_COOLDOWN_HOURS = int(os.environ.get("ALERT_COOLDOWN_HOURS", "12"))

# Load snowfall thresholds
THRESHOLD_LIGHT = float(os.environ.get("THRESHOLD_LIGHT", "2"))
THRESHOLD_MODERATE = float(os.environ.get("THRESHOLD_MODERATE", "6"))
THRESHOLD_HEAVY = float(os.environ.get("THRESHOLD_HEAVY", "12"))

# Check frequency (in hours) - for testing purposes
CHECK_FREQUENCY = int(os.environ.get("CHECK_FREQUENCY", "6"))


# Required Environment Variables Check
def validate_config() -> List[str]:
    """
    Validate that all required configuration variables are set.

    Returns:
        List of missing configuration variables
    """
    missing = []

    if not OPENWEATHER_API_KEY:
        missing.append("OPENWEATHER_API_KEY")

    if not WEATHERAPI_KEY:
        missing.append("WEATHERAPI_KEY")

    if not SLACK_WEBHOOK_URL:
        missing.append("SLACK_WEBHOOK_URL")

    return missing
