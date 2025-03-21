"""
Resort data validation utilities for the Snowfall Alert System.

This module provides functions to validate resort data, ensuring
that the required fields are present and in the correct format.
"""

from typing import Dict, Any, List, Tuple
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Required fields for each resort
REQUIRED_FIELDS = ["coordinates", "elevation", "website"]

# Optional fields that are nice to have but not required
OPTIONAL_FIELDS = ["region", "type", "vertical_drop"]


def validate_resort_data(
    resort_name: str, resort_data: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate the data for a single resort.

    Args:
        resort_name: Name of the resort
        resort_data: Dictionary of resort data

    Returns:
        Tuple containing:
        - Boolean indicating if the data is valid
        - List of validation error messages (empty if valid)
    """
    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in resort_data:
            errors.append(f"Missing required field: {field}")

    # Check coordinates
    if "coordinates" in resort_data:
        coords = resort_data["coordinates"]
        if not isinstance(coords, tuple) or len(coords) != 2:
            errors.append("Coordinates must be a tuple of (latitude, longitude)")
        elif not all(isinstance(c, (int, float)) for c in coords):
            errors.append("Coordinates must be numeric values")
        elif not (-90 <= coords[0] <= 90 and -180 <= coords[1] <= 180):
            errors.append(
                "Coordinates out of valid range (latitude: -90 to 90, longitude: -180 to 180)"
            )

    # Check elevation
    if "elevation" in resort_data:
        elevation = resort_data["elevation"]
        if not isinstance(elevation, (int, float)):
            errors.append("Elevation must be a numeric value")
        elif elevation < 0 or elevation > 30000:  # Mount Everest is ~29,000 feet
            errors.append("Elevation out of reasonable range (0 to 30,000 feet)")

    # Check website
    if "website" in resort_data:
        website = resort_data["website"]
        if not isinstance(website, str):
            errors.append("Website must be a string")
        elif not website.startswith(("http://", "https://")):
            errors.append("Website URL must start with http:// or https://")

    # Check optional fields
    for field in OPTIONAL_FIELDS:
        if field in resort_data:
            if field == "vertical_drop" and not isinstance(
                resort_data[field], (int, float)
            ):
                errors.append(f"Field '{field}' must be a numeric value")
            elif field in ["region", "type"] and not isinstance(
                resort_data[field], str
            ):
                errors.append(f"Field '{field}' must be a string")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(
            f"Validation failed for resort '{resort_name}': {', '.join(errors)}"
        )

    return is_valid, errors


def validate_all_resorts(resorts: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Validate all resorts in a dictionary.

    Args:
        resorts: Dictionary mapping resort names to resort data

    Returns:
        Dictionary mapping resort names to lists of error messages (empty if valid)
    """
    all_errors = {}
    all_valid = True

    for name, data in resorts.items():
        is_valid, errors = validate_resort_data(name, data)
        if not is_valid:
            all_errors[name] = errors
            all_valid = False

    if all_valid:
        logger.info("All resorts passed validation")
    else:
        logger.warning(f"{len(all_errors)} resorts failed validation")

    return all_errors
