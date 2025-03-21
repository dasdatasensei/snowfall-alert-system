"""
Environment Variables Validation Module.

This module provides functions to validate that all required environment variables
are properly set before the application starts, to avoid any issues with missing or
hardcoded credentials.
"""

import os
import sys
import logging
from typing import Dict, List, Set, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Required variable groups with their descriptions
REQUIRED_VARS = {
    "API_KEYS": {
        "description": "API Keys for weather data providers",
        "variables": [
            "OPENWEATHER_API_KEY",
            "WEATHERAPI_KEY",
        ],
    },
    "NOTIFICATION": {
        "description": "Notification service credentials",
        "variables": [
            "SLACK_WEBHOOK_URL",
            "SLACK_MONITORING_WEBHOOK_URL",
        ],
    },
    "AWS": {
        "description": "AWS configuration",
        "variables": [
            "AWS_REGION",
            "AWS_ENDPOINT_URL",
        ],
    },
    "DATABASE": {
        "description": "Database configuration",
        "variables": [
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
            "DB_PORT",
        ],
    },
    "LAMBDA": {
        "description": "Lambda configuration",
        "variables": [
            "LAMBDA_FUNCTION_NAME",
            "LAMBDA_RUNTIME",
            "LAMBDA_HANDLER",
            "LAMBDA_ROLE",
        ],
    },
}

# Environment-specific required variable groups
ENV_SPECIFIC_VARS = {
    "development": ["API_KEYS", "NOTIFICATION", "AWS", "DATABASE"],
    "test": ["API_KEYS", "AWS", "DATABASE"],
    "production": ["API_KEYS", "NOTIFICATION", "AWS", "LAMBDA"],
}


def get_environment() -> str:
    """
    Determine the current environment.

    Returns:
        str: One of 'development', 'test', or 'production'
    """
    env = os.environ.get("ENVIRONMENT", "development").lower()
    if env not in ENV_SPECIFIC_VARS:
        logger.warning(f"Unknown environment: {env}, defaulting to development")
        env = "development"
    return env


def get_missing_variables(required_groups: List[str]) -> Dict[str, List[str]]:
    """
    Check for missing environment variables.

    Args:
        required_groups: List of required variable groups for the environment

    Returns:
        Dict mapping group names to lists of missing variables
    """
    missing_vars = {}

    for group in required_groups:
        if group not in REQUIRED_VARS:
            logger.warning(f"Unknown variable group: {group}")
            continue

        group_vars = REQUIRED_VARS[group]["variables"]
        missing = [var for var in group_vars if not os.environ.get(var)]

        if missing:
            missing_vars[group] = missing

    return missing_vars


def validate_environment_variables(exit_on_missing: bool = False) -> bool:
    """
    Validate that all required environment variables are set.

    Args:
        exit_on_missing: Whether to exit the program if variables are missing

    Returns:
        bool: True if all required variables are set, False otherwise
    """
    environment = get_environment()
    required_groups = ENV_SPECIFIC_VARS[environment]
    missing_vars = get_missing_variables(required_groups)

    if not missing_vars:
        logger.info(
            f"All required environment variables for {environment} environment are set"
        )
        return True

    # Log missing variables
    logger.error(f"Missing environment variables for {environment} environment:")
    for group, vars in missing_vars.items():
        group_desc = REQUIRED_VARS[group]["description"]
        logger.error(f"  {group} - {group_desc}:")
        for var in vars:
            logger.error(f"    - {var}")

    if exit_on_missing:
        logger.error("Exiting due to missing environment variables")
        sys.exit(1)

    return False


def check_for_default_values() -> List[str]:
    """
    Check if any environment variables contain default example values.

    Returns:
        List of variables with potentially default values
    """
    suspicious_values = []

    # Patterns that suggest default/example values
    suspicious_patterns = [
        "your_",
        "example",
        "change_me",
        "change_this",
        "changeme",
        "xxxx",
        "test",
        "secret",
        "password123",
        "123456",
    ]

    # Check API keys for suspicious patterns or common test values
    for var in ["OPENWEATHER_API_KEY", "WEATHERAPI_KEY", "SLACK_WEBHOOK_URL"]:
        value = os.environ.get(var, "")
        if value:
            # Check for suspicious patterns
            for pattern in suspicious_patterns:
                if pattern in value.lower():
                    suspicious_values.append(f"{var} (contains '{pattern}')")
                    break

            # Check for other issues like very short values
            if len(value) < 8 and value not in ("", "0", "false", "true"):
                suspicious_values.append(f"{var} (suspiciously short)")

    return suspicious_values


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Validate environment variables
    validate_environment_variables(exit_on_missing=True)

    # Check for suspicious default values
    suspicious = check_for_default_values()
    if suspicious:
        logger.warning("The following variables may contain default/example values:")
        for var in suspicious:
            logger.warning(f"  - {var}")
