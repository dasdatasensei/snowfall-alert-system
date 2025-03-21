"""
Coordinate validation utilities for the Snowfall Alert System.

This module provides functions to validate resort coordinates against
the weather APIs to ensure they return valid data.
"""

import os
import requests
import time
from typing import Dict, Any, List, Tuple, Optional

from src.utils.logging import get_logger, ExecutionTimer
from src.config.settings import OPENWEATHER_API_KEY, WEATHERAPI_KEY

logger = get_logger(__name__)


def validate_coordinates_with_openweathermap(
    lat: float, lon: float
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate coordinates against OpenWeatherMap API.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple containing:
        - Boolean indicating if the coordinates are valid
        - Response data if valid, None otherwise
    """
    if not OPENWEATHER_API_KEY:
        logger.error("OpenWeatherMap API key not configured")
        return False, None

    try:
        # Construct the API URL for current weather (simplest endpoint)
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "imperial",
        }

        logger.info(f"Validating coordinates ({lat}, {lon}) with OpenWeatherMap")

        # Make the API request
        with ExecutionTimer("validate_openweathermap", logger):
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

        # Check if the response contains basic weather data
        if "name" in data and "weather" in data and "main" in data:
            logger.info(
                f"Coordinates valid for OpenWeatherMap: ({lat}, {lon}) - Location: {data.get('name')}"
            )
            return True, data
        else:
            logger.warning(
                f"Coordinates ({lat}, {lon}) returned incomplete data from OpenWeatherMap"
            )
            return False, data

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to validate coordinates with OpenWeatherMap: {e}")
        return False, None
    except Exception as e:
        logger.error(
            f"Unexpected error validating coordinates with OpenWeatherMap: {e}"
        )
        return False, None


def validate_coordinates_with_weatherapi(
    lat: float, lon: float
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate coordinates against WeatherAPI.com.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple containing:
        - Boolean indicating if the coordinates are valid
        - Response data if valid, None otherwise
    """
    if not WEATHERAPI_KEY:
        logger.error("WeatherAPI.com API key not configured")
        return False, None

    try:
        # Construct the API URL
        url = f"https://api.weatherapi.com/v1/current.json"
        params = {"q": f"{lat},{lon}", "key": WEATHERAPI_KEY}

        logger.info(f"Validating coordinates ({lat}, {lon}) with WeatherAPI.com")

        # Add a slight delay to respect rate limiting
        time.sleep(1)

        # Make the API request
        with ExecutionTimer("validate_weatherapi", logger):
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

        # Check if the response contains location data
        if "location" in data and "name" in data["location"]:
            logger.info(
                f"Coordinates valid for WeatherAPI.com: ({lat}, {lon}) - Location: {data['location'].get('name')}"
            )
            return True, data
        else:
            logger.warning(
                f"Coordinates ({lat}, {lon}) returned incomplete data from WeatherAPI.com"
            )
            return False, data

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to validate coordinates with WeatherAPI.com: {e}")
        return False, None
    except Exception as e:
        logger.error(
            f"Unexpected error validating coordinates with WeatherAPI.com: {e}"
        )
        return False, None


def validate_resort_coordinates(
    resort_name: str, coordinates: Tuple[float, float]
) -> Dict[str, Any]:
    """
    Validate resort coordinates against both weather APIs.

    Args:
        resort_name: Name of the resort
        coordinates: Tuple of (latitude, longitude)

    Returns:
        Dictionary with validation results
    """
    lat, lon = coordinates

    results = {
        "resort": resort_name,
        "coordinates": coordinates,
        "openweathermap_valid": False,
        "weatherapi_valid": False,
        "both_valid": False,
        "location_names": {},
        "errors": [],
    }

    # Validate with OpenWeatherMap
    owm_valid, owm_data = validate_coordinates_with_openweathermap(lat, lon)
    results["openweathermap_valid"] = owm_valid
    if owm_valid and owm_data:
        results["location_names"]["openweathermap"] = owm_data.get("name", "Unknown")
    elif not owm_valid:
        results["errors"].append("Failed validation with OpenWeatherMap")

    # Validate with WeatherAPI.com
    wa_valid, wa_data = validate_coordinates_with_weatherapi(lat, lon)
    results["weatherapi_valid"] = wa_valid
    if wa_valid and wa_data and "location" in wa_data:
        results["location_names"]["weatherapi"] = wa_data["location"].get(
            "name", "Unknown"
        )
    elif not wa_valid:
        results["errors"].append("Failed validation with WeatherAPI.com")

    # Both APIs valid
    results["both_valid"] = owm_valid and wa_valid

    return results


def validate_all_resort_coordinates(
    resorts: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Validate coordinates for all resorts.

    Args:
        resorts: Dictionary mapping resort names to resort data

    Returns:
        Dictionary mapping resort names to validation results
    """
    results = {}

    for name, data in resorts.items():
        if "coordinates" in data:
            logger.info(f"Validating coordinates for {name}")
            results[name] = validate_resort_coordinates(name, data["coordinates"])
        else:
            logger.warning(f"Resort {name} missing coordinates, skipping validation")
            results[name] = {
                "resort": name,
                "coordinates": None,
                "openweathermap_valid": False,
                "weatherapi_valid": False,
                "both_valid": False,
                "errors": ["Missing coordinates"],
            }

    # Summary
    valid_count = sum(1 for r in results.values() if r.get("both_valid", False))
    logger.info(
        f"Coordinate validation complete: {valid_count}/{len(resorts)} resorts valid with both APIs"
    )

    return results


# Command-line interface for testing
if __name__ == "__main__":
    from src.config.resorts import RESORTS

    # Create a smaller subset for testing
    test_resorts = {
        name: data for name, data in list(RESORTS.items())[:3]  # First 3 resorts
    }

    # Run validation
    results = validate_all_resort_coordinates(test_resorts)

    # Print results
    for name, result in results.items():
        status = "✓" if result["both_valid"] else "✗"
        print(
            f"{status} {name}: OWM={result['openweathermap_valid']}, WA={result['weatherapi_valid']}"
        )
        if "location_names" in result and result["location_names"]:
            print(f"  Locations: {result['location_names']}")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")
