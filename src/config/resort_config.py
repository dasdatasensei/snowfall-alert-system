"""
Resort configuration management for the Snowfall Alert System.

This module provides utilities for managing resort configurations,
including loading, filtering, and validating resort data.
"""

import os
import json
from typing import Dict, Any, List, Tuple, Optional

from src.utils.logging import get_logger
from src.config.resorts import RESORTS

logger = get_logger(__name__)

# Get enabled resorts from environment variable
ENABLED_RESORTS_STR = os.environ.get("ENABLED_RESORTS", "")
ENABLED_RESORTS = (
    [r.strip() for r in ENABLED_RESORTS_STR.split(",")] if ENABLED_RESORTS_STR else None
)


def get_enabled_resorts() -> Dict[str, Dict[str, Any]]:
    """
    Get the enabled resorts based on configuration.

    Returns:
        Dictionary of enabled resorts with their data
    """
    if not ENABLED_RESORTS:
        logger.info("No specific resorts enabled, using all configured resorts")
        return RESORTS

    enabled = {}
    for resort_name in ENABLED_RESORTS:
        if resort_name in RESORTS:
            enabled[resort_name] = RESORTS[resort_name]
            logger.debug(f"Enabled resort: {resort_name}")
        else:
            logger.warning(
                f"Resort '{resort_name}' specified in ENABLED_RESORTS but not found in configuration"
            )

    logger.info(f"Enabled {len(enabled)} out of {len(RESORTS)} configured resorts")
    return enabled


def get_resort_by_region(region: str) -> Dict[str, Dict[str, Any]]:
    """
    Get resorts in a specific region.

    Args:
        region: The region name to filter by

    Returns:
        Dictionary of resorts in the specified region
    """
    return {
        name: data for name, data in RESORTS.items() if data.get("region") == region
    }


def get_resort_coordinates(resort_name: str) -> Tuple[float, float]:
    """
    Get coordinates for a specific resort.

    Args:
        resort_name: Name of the resort

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        KeyError: If the resort is not found
    """
    if resort_name not in RESORTS:
        raise KeyError(f"Resort '{resort_name}' not found in configuration")

    return RESORTS[resort_name]["coordinates"]


def save_resort_data(resort_name: str, data_key: str, data_value: Any) -> bool:
    """
    Save additional data for a resort (for future enhancement).

    In a production system, this would save to a database or persistent store.

    Args:
        resort_name: Name of the resort
        data_key: Key for the data
        data_value: Value to store

    Returns:
        Success status
    """
    # This is a placeholder for future functionality
    logger.info(f"Would save {data_key}={data_value} for {resort_name}")
    return True


def export_resorts_to_json(filepath: str) -> bool:
    """
    Export all resort data to a JSON file.

    Args:
        filepath: Path to the output JSON file

    Returns:
        Success status
    """
    try:
        with open(filepath, "w") as f:
            json.dump(RESORTS, f, indent=2)
        logger.info(f"Exported resort data to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to export resort data: {e}")
        return False


def import_resorts_from_json(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    Import resort data from a JSON file.

    Args:
        filepath: Path to the input JSON file

    Returns:
        Dictionary of imported resort data

    Raises:
        Exception: If the file cannot be read or parsed
    """
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        logger.info(f"Imported resort data from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Failed to import resort data: {e}")
        raise
