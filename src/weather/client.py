"""
Weather API client classes for the Snowfall Alert System.

This module provides client classes for interacting with weather APIs,
handling authentication, request formation, response parsing, and error handling.
"""

import os
import time
import json
import hashlib
from datetime import datetime, timedelta
import requests
from typing import Dict, Any, Optional, Tuple, List
from functools import lru_cache

from src.utils.logging import get_logger, ExecutionTimer
from src.config.settings import (
    OPENWEATHER_API_KEY,
    WEATHERAPI_KEY,
    VERIFICATION_THRESHOLD,
)

# Initialize logger
logger = get_logger(__name__)

# Cache TTL (in seconds)
CACHE_TTL = int(os.environ.get("CACHE_TTL", "300"))  # 5 minutes default


class WeatherAPIClient:
    """Base class for weather API clients with common functionality."""

    def __init__(self, api_key: str, base_url: str, cache_enabled: bool = True):
        """
        Initialize the API client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for API requests
            cache_enabled: Whether to enable response caching
        """
        self.api_key = api_key
        self.base_url = base_url
        self.cache_enabled = cache_enabled
        self.session = requests.Session()
        self.cache = {}
        self.cache_expiry = {}

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Generate a unique cache key for a request.

        Args:
            endpoint: API endpoint
            params: Request parameters

        Returns:
            String cache key
        """
        # Create a consistent string representation of the params
        params_str = json.dumps(params, sort_keys=True)
        # Create a hash for the cache key
        key = hashlib.md5(f"{endpoint}:{params_str}".encode()).hexdigest()
        return key

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if a cached response is still valid.

        Args:
            cache_key: Cache key to check

        Returns:
            Boolean indicating if cache is valid
        """
        # Check if key exists in both cache and expiry
        if cache_key not in self.cache or cache_key not in self.cache_expiry:
            return False

        # Check if cache entry has expired
        return datetime.now() < self.cache_expiry[cache_key]

    def _cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """
        Cache an API response.

        Args:
            cache_key: Cache key
            response: Response data to cache
        """
        self.cache[cache_key] = response
        self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=CACHE_TTL)

    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Make an API request with retry logic and caching.

        Args:
            endpoint: API endpoint to call
            params: Request parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (doubles each attempt)

        Returns:
            Parsed API response

        Raises:
            Exception: If all retry attempts fail
        """
        params = params or {}
        url = f"{self.base_url}/{endpoint}"

        # Check cache if enabled
        if self.cache_enabled:
            cache_key = self._get_cache_key(endpoint, params)
            if self._is_cache_valid(cache_key):
                logger.debug(f"Using cached response for {endpoint}")
                return self.cache[cache_key]

        # Make request with retry logic
        retries = 0
        last_exception = None

        while retries < max_retries:
            try:
                with ExecutionTimer(f"api_request_{endpoint}", logger):
                    logger.debug(f"Making request to {url} with params {params}")
                    response = self.session.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                # Cache successful response if caching is enabled
                if self.cache_enabled:
                    cache_key = self._get_cache_key(endpoint, params)
                    self._cache_response(cache_key, data)

                return data

            except requests.exceptions.RequestException as e:
                last_exception = e
                retries += 1

                if retries < max_retries:
                    sleep_time = retry_delay * (
                        2 ** (retries - 1)
                    )  # Exponential backoff
                    logger.warning(
                        f"Request failed, retrying in {sleep_time:.1f}s ({retries}/{max_retries}): {str(e)}"
                    )
                    time.sleep(sleep_time)
                else:
                    logger.error(
                        f"Request failed after {max_retries} attempts: {str(e)}"
                    )

        # If all retries failed, raise the last exception
        raise last_exception or Exception(f"Request to {url} failed for unknown reason")


class OpenWeatherMapClient(WeatherAPIClient):
    """Client for the OpenWeatherMap API."""

    def __init__(self, api_key: str = None, cache_enabled: bool = True):
        """
        Initialize the OpenWeatherMap client.

        Args:
            api_key: API key (defaults to environment variable)
            cache_enabled: Whether to enable response caching
        """
        super().__init__(
            api_key=api_key or OPENWEATHER_API_KEY,
            base_url="https://api.openweathermap.org/data/2.5",
            cache_enabled=cache_enabled,
        )

    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get current weather data for a specific location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Current weather data
        """
        params = {
            "lat": lat,
            "lon": lon,
            "units": "imperial",  # Use imperial units for inches
            "appid": self.api_key,
        }

        return self._make_request("weather", params)

    def get_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get 5-day forecast data using the free forecast endpoint.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Weather forecast data
        """
        params = {
            "lat": lat,
            "lon": lon,
            "units": "imperial",  # Use imperial units for inches
            "appid": self.api_key,
        }

        return self._make_request("forecast", params)

    def get_one_call_data(
        self, lat: float, lon: float, exclude: str = "minutely,hourly"
    ) -> Dict[str, Any]:
        """
        Get comprehensive weather data using the One Call API.
        Note: This requires a paid subscription to the OneCall API.

        Args:
            lat: Latitude
            lon: Longitude
            exclude: Sections to exclude from the response

        Returns:
            Weather data including current conditions and forecast
        """
        logger.warning("OneCall API requires a separate paid subscription")
        params = {
            "lat": lat,
            "lon": lon,
            "units": "imperial",  # Use imperial units for inches
            "exclude": exclude,
            "appid": self.api_key,
        }

        return self._make_request("onecall", params)

    def get_snow_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get snowfall data for a specific location using free API endpoints.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with current and forecast snow data
        """
        try:
            # Try to use the free endpoints instead of OneCall
            current_data = self.get_current_weather(lat, lon)
            forecast_data = self.get_forecast(lat, lon)

            # Extract current snow (if available in the response)
            current_snow = current_data.get("snow", {}).get("1h", 0)
            if not current_snow:
                current_snow = current_data.get("snow", 0)  # Try alternate format

            # Extract forecast snow from the next day's forecast
            forecast_snow = 0
            # Look through forecast list (which has 3-hour intervals)
            # and sum up the snow for the next 24 hours
            for period in forecast_data.get("list", [])[:8]:  # 8 periods = 24 hours
                period_snow = period.get("snow", {}).get("3h", 0)
                if not period_snow and isinstance(period.get("snow"), (int, float)):
                    period_snow = period.get("snow", 0)
                forecast_snow += period_snow

            # Get additional data points
            current_temp = current_data.get("main", {}).get("temp", 0)
            conditions = current_data.get("weather", [{}])[0].get("description", "")

            return {
                "current_snow": current_snow,
                "forecast_snow": forecast_snow,
                "current_temp": current_temp,
                "conditions": conditions,
                "timestamp": datetime.now().isoformat(),
                "source": "OpenWeatherMap (Free API)",
            }

        except Exception as e:
            logger.error(f"Error getting snow data from free endpoints: {str(e)}")
            # Fall back to using WeatherAPI as the primary source
            try:
                weather_api_client = WeatherApiClient()
                secondary_data = weather_api_client.get_snow_data(lat, lon)

                # Convert to expected format
                return {
                    "current_snow": secondary_data.get("snow_inches", 0),
                    "forecast_snow": 0,  # Limited forecast info in free tier
                    "current_temp": secondary_data.get("current_temp", 0),
                    "conditions": secondary_data.get("conditions", ""),
                    "timestamp": datetime.now().isoformat(),
                    "source": "Fallback: WeatherAPI.com",
                }
            except Exception as fallback_error:
                logger.error(
                    f"Fallback to WeatherAPI also failed: {str(fallback_error)}"
                )
                # Return a default response with zero values to avoid breaking the app
                return {
                    "current_snow": 0,
                    "forecast_snow": 0,
                    "current_temp": 0,
                    "conditions": "Error fetching data",
                    "timestamp": datetime.now().isoformat(),
                    "source": "Default values (API errors)",
                }


class WeatherApiClient(WeatherAPIClient):
    """Client for WeatherAPI.com."""

    def __init__(self, api_key: str = None, cache_enabled: bool = True):
        """
        Initialize the WeatherAPI.com client.

        Args:
            api_key: API key (defaults to environment variable)
            cache_enabled: Whether to enable response caching
        """
        super().__init__(
            api_key=api_key or WEATHERAPI_KEY,
            base_url="https://api.weatherapi.com/v1",
            cache_enabled=cache_enabled,
        )

    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get current weather data for a specific location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Current weather data
        """
        params = {"q": f"{lat},{lon}", "key": self.api_key}

        return self._make_request("current.json", params)

    def get_forecast(self, lat: float, lon: float, days: int = 1) -> Dict[str, Any]:
        """
        Get weather forecast for a specific location.

        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days to forecast (1-3 for free tier)

        Returns:
            Forecast data
        """
        params = {"q": f"{lat},{lon}", "days": days, "key": self.api_key}

        return self._make_request("forecast.json", params)

    def get_snow_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get snowfall data for a specific location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with snow data
        """
        data = self.get_forecast(lat, lon, days=1)

        # Extract snow data (in cm, convert to inches)
        snow_cm = (
            data.get("forecast", {})
            .get("forecastday", [{}])[0]
            .get("day", {})
            .get("totalsnow_cm", 0)
        )
        snow_inches = snow_cm / 2.54  # Convert cm to inches

        # Get additional data
        current_temp_f = data.get("current", {}).get("temp_f", 0)
        conditions = data.get("current", {}).get("condition", {}).get("text", "")

        return {
            "snow_cm": snow_cm,
            "snow_inches": snow_inches,
            "current_temp": current_temp_f,
            "conditions": conditions,
            "timestamp": datetime.now().isoformat(),
            "source": "WeatherAPI.com",
        }


# Helper functions for using the clients together


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
            # Create client and get snow data
            client = OpenWeatherMapClient()
            snow_data = client.get_snow_data(lat, lon)

            # Add resort name to the data
            snow_data["resort"] = resort_name

            logger.info(
                f"Retrieved snow data for {resort_name}",
                current_snow=snow_data["current_snow"],
                forecast_snow=snow_data["forecast_snow"],
            )

            return snow_data

        except Exception as e:
            logger.error(f"Failed to get snow data for {resort_name}: {str(e)}")
            raise Exception(f"Failed to retrieve weather data: {str(e)}")


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

            # Create client and get snow data
            client = WeatherApiClient()
            secondary_data = client.get_snow_data(lat, lon)

            # Add resort name to the data
            secondary_data["resort"] = resort_name

            snow_inches = secondary_data["snow_inches"]

            logger.info(
                f"Secondary source data for {resort_name}",
                primary_inches=primary_snow_amount,
                secondary_inches=snow_inches,
                difference=abs(primary_snow_amount - snow_inches),
            )

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


# Allow direct execution for testing
if __name__ == "__main__":
    # Test the OpenWeatherMap client
    owm_client = OpenWeatherMapClient()
    lat, lon = 40.6514, -111.5080  # Park City

    try:
        snow_data = owm_client.get_snow_data(lat, lon)
        print("OpenWeatherMap Snow Data:")
        print(json.dumps(snow_data, indent=2))
    except Exception as e:
        print(f"Error testing OpenWeatherMap: {e}")

    # Test the WeatherAPI client
    wa_client = WeatherApiClient()

    try:
        snow_data = wa_client.get_snow_data(lat, lon)
        print("\nWeatherAPI.com Snow Data:")
        print(json.dumps(snow_data, indent=2))
    except Exception as e:
        print(f"Error testing WeatherAPI: {e}")

    # Test verification
    try:
        is_verified, secondary_data = verify_with_secondary_source(
            "Test Resort", lat, lon, 5.0
        )
        print(f"\nVerification result: {is_verified}")
        if secondary_data:
            print(json.dumps(secondary_data, indent=2))
    except Exception as e:
        print(f"Error testing verification: {e}")
