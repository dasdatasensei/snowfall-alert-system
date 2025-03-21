"""
Configuration package for the Snowfall Alert System.
"""

from src.config.settings import (
    OPENWEATHER_API_KEY,
    WEATHERAPI_KEY,
    SLACK_WEBHOOK_URL,
    SLACK_MONITORING_WEBHOOK_URL,
    LOG_LEVEL,
    VERIFICATION_THRESHOLD,
    ALERT_COOLDOWN_HOURS,
    THRESHOLD_LIGHT,
    THRESHOLD_MODERATE,
    THRESHOLD_HEAVY,
    CHECK_FREQUENCY,
    validate_config,
)

from src.config.resorts import RESORTS, RESORT_COORDINATES
from src.config.resort_config import (
    get_enabled_resorts,
    get_resort_by_region,
    get_resort_coordinates,
    export_resorts_to_json,
    import_resorts_from_json,
)
from src.config.thresholds import THRESHOLDS

__all__ = [
    # Settings
    "OPENWEATHER_API_KEY",
    "WEATHERAPI_KEY",
    "SLACK_WEBHOOK_URL",
    "SLACK_MONITORING_WEBHOOK_URL",
    "LOG_LEVEL",
    "VERIFICATION_THRESHOLD",
    "ALERT_COOLDOWN_HOURS",
    "THRESHOLD_LIGHT",
    "THRESHOLD_MODERATE",
    "THRESHOLD_HEAVY",
    "CHECK_FREQUENCY",
    "validate_config",
    # Resorts
    "RESORTS",
    "RESORT_COORDINATES",
    "get_enabled_resorts",
    "get_resort_by_region",
    "get_resort_coordinates",
    "export_resorts_to_json",
    "import_resorts_from_json",
    # Thresholds
    "THRESHOLDS",
]
