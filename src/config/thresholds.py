"""
Snowfall thresholds configuration for the Snowfall Alert System.

This module defines the snowfall thresholds that trigger different levels of alerts.
Thresholds can be overridden using environment variables.
"""

import os

# Snowfall thresholds for alerts (in inches)
# These values can be overridden with environment variables
THRESHOLDS = {
    "light": float(os.environ.get("THRESHOLD_LIGHT", "2")),  # 2+ inches in 24 hours
    "moderate": float(
        os.environ.get("THRESHOLD_MODERATE", "6")
    ),  # 6+ inches in 24 hours
    "heavy": float(os.environ.get("THRESHOLD_HEAVY", "12")),  # 12+ inches in 24 hours
}
