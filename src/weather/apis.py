"""
Weather API integration for the Snowfall Alert System.

This module provides functions to retrieve snowfall data from multiple weather APIs
and perform verification across sources.
"""

import os
import time
import requests
from typing import Dict, Tuple, Optional, Any
from datetime import datetime
import logging

from src.utils.logging import get_logger, ExecutionTimer

# Initialize logger
logger = get_logger(__name__)

# API keys from environment variables
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
WEATHERAPI_KEY = os.environ.get("WEATHERAPI_KEY", "")

# Verification threshold (in inches) - maximum allowable difference between sources
VERIFICATION_THRESHOLD = float(os.environ.get("VERIFICATION_THRESHOLD", "2.0"))


def get_resort_snow_data(resort_name: str, lat: float, lon: float) -> Dict[str, Any]:
    """
    Get snowfall data for a specific resort from OpenWeatherMap API.

    Args:
        resort_name: Name of the resort
        lat: Latitude of the resort
        lon: Longitude of the resort

    Returns:
        Dictionary containing snow data for the resort

    Raises:
        Exception: If API request fails or data can't be parsed
    """
    with ExecutionTimer(f"get_snow_data_{resort_name}", logger):
        try:
            # Construct the API URL
            url = (
                f"https://api.openweathermap.org/data/2.5/onecall"
                f"?lat={lat}&lon={lon}"
                f"&exclude=minutely,hourly"
                f"&units=imperial"
                f"&appid={OPENWEATHER_API_KEY}"
            )

            logger.info(f"Requesting data from OpenWeatherMap for {resort_name}")

            # Make the API request
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors

            # Parse the response
            data = response.json()

            # Extract snow data (past 24h from daily data)
            current_snow = data.get("daily", [{}])[0].get("snow", 0)

            # Extract forecast snow (next 24-48h)
            forecast_snow = sum(
                day.get("snow", 0) for day in data.get("daily", [])[1:2]
            )

            # Get additional data points
            current_temp = data.get("current", {}).get("temp", 0)
            conditions = (
                data.get("current", {}).get("weather", [{}])[0].get("description", "")
            )

            # Create a complete data dictionary
            snow_data = {
                "resort": resort_name,
                "current_snow": current_snow,
                "forecast_snow": forecast_snow,
                "current_temp": current_temp,
                "conditions": conditions,
                "timestamp": datetime.now().isoformat(),
                "source": "OpenWeatherMap",
            }

            logger.info(
                f"Retrieved snow data for {resort_name}",
                current_snow=current_snow,
                forecast_snow=forecast_snow,
            )

            return snow_data

        except requests.exceptions.RequestException as e:
            logger.error(f"API request error for {resort_name}: {e}")
            raise Exception(f"Failed to retrieve weather data: {str(e)}")
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Data parsing error for {resort_name}: {e}")
            raise Exception(f"Failed to parse weather data: {str(e)}")


def verify_with_secondary_source(
    resort_name: str, lat: float, lon: float, primary_snow_amount: float
) -> Tuple[bool, Optional[Dict]]:
    """
    Verify snow data with a secondary source (WeatherAPI.com).

    Args:
        resort_name: Name of the resort
        lat: Latitude of the resort
        lon: Longitude of the resort
        primary_snow_amount: Snow amount from primary source

    Returns:
        Tuple containing:
        - Boolean indicating if the snow amount is verified
        - Dictionary with the secondary source data (or None if verification failed)
    """
    with ExecutionTimer(f"verify_snow_{resort_name}", logger):
        try:
            # Add a small delay to respect rate limits
            time.sleep(1)

            # Construct the API URL
            url = (
                f"https://api.weatherapi.com/v1/forecast.json"
                f"?key={WEATHERAPI_KEY}"
                f"&q={lat},{lon}"
                f"&days=1"
            )

            logger.info(f"Verifying snow data for {resort_name} with WeatherAPI.com")

            # Make the API request
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse the response
            data = response.json()

            # Extract snow data (in cm, convert to inches)
            snow_cm = (
                data.get("forecast", {})
                .get("forecastday", [{}])[0]
                .get("day", {})
                .get("totalsnow_cm", 0)
            )
            snow_inches = snow_cm / 2.54  # Convert cm to inches

            logger.info(
                f"Secondary source data for {resort_name}",
                primary_inches=primary_snow_amount,
                secondary_inches=snow_inches,
                difference=abs(primary_snow_amount - snow_inches),
            )

            # Create the secondary data dictionary
            secondary_data = {
                "resort": resort_name,
                "snow_cm": snow_cm,
                "snow_inches": snow_inches,
                "timestamp": datetime.now().isoformat(),
                "source": "WeatherAPI.com",
            }

            # Check if the snow amounts are within the verification threshold
            if abs(primary_snow_amount - snow_inches) <= VERIFICATION_THRESHOLD:
                logger.info(f"Snow data verified for {resort_name}")
                return True, secondary_data
            else:
                logger.info(
                    f"Snow data verification failed for {resort_name} - amounts differ by more than threshold",
                    threshold=VERIFICATION_THRESHOLD,
                )
                return False, secondary_data

        except Exception as e:
            logger.error(f"Verification error for {resort_name}: {e}")
            return False, None
