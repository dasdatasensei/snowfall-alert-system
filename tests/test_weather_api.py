"""
Tests for the weather API integration.

This module contains tests for the weather API client classes and helper functions.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
import responses
from datetime import datetime, timedelta

from src.weather.client import (
    WeatherAPIClient,
    OpenWeatherMapClient,
    WeatherApiClient,
    get_resort_snow_data,
    verify_with_secondary_source,
)


# Test the base WeatherAPIClient class
class TestWeatherAPIClient:
    def setup_method(self):
        self.client = WeatherAPIClient(
            api_key="test_key", base_url="https://api.example.com", cache_enabled=True
        )

    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        params1 = {"param1": "value1", "param2": "value2"}
        params2 = {
            "param2": "value2",
            "param1": "value1",
        }  # Same params, different order

        key1 = self.client._get_cache_key("endpoint", params1)
        key2 = self.client._get_cache_key("endpoint", params2)

        # Keys should be the same despite different param order
        assert key1 == key2

        # Different endpoint should give different key
        key3 = self.client._get_cache_key("different", params1)
        assert key1 != key3

    def test_cache_validity(self):
        """Test cache validity checking."""
        # Cache should be invalid for non-existent key
        assert not self.client._is_cache_valid("nonexistent")

        # Add a cache entry
        cache_key = "test_key"
        self.client.cache[cache_key] = {"data": "test"}
        # Set expiry in the future (5 minutes from now)
        self.client.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)

        # Should be valid as it's not expired yet
        assert self.client._is_cache_valid(cache_key)

        # Create a key with an expired entry
        expired_key = "expired_key"
        self.client.cache[expired_key] = {"data": "test"}
        # Set expiry in the past
        self.client.cache_expiry[expired_key] = datetime.now() - timedelta(minutes=5)

        # Should be invalid as it's expired
        assert not self.client._is_cache_valid(expired_key)

    @responses.activate
    def test_make_request_success(self):
        """Test successful API request."""
        endpoint = "test"
        url = f"{self.client.base_url}/{endpoint}"
        test_data = {"result": "success"}

        # Mock response
        responses.add(responses.GET, url, json=test_data, status=200)

        # Make request
        result = self.client._make_request(endpoint, {"test": "param"})

        # Check result
        assert result == test_data

        # Check cache
        cache_key = self.client._get_cache_key(endpoint, {"test": "param"})
        assert cache_key in self.client.cache
        assert self.client.cache[cache_key] == test_data

    @responses.activate
    def test_make_request_retry(self):
        """Test request retry logic."""
        endpoint = "test"
        url = f"{self.client.base_url}/{endpoint}"
        test_data = {"result": "success"}

        # Add a failing response followed by a successful one
        responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, json=test_data, status=200)

        # Make request (should retry and succeed)
        with patch("time.sleep", return_value=None):  # Don't actually sleep in tests
            result = self.client._make_request(
                endpoint, {"test": "param"}, retry_delay=0.1
            )

        # Check result
        assert result == test_data

    @responses.activate
    def test_make_request_cache_hit(self):
        """Test cache hit prevents API request."""
        endpoint = "test"
        url = f"{self.client.base_url}/{endpoint}"
        test_data = {"result": "cached"}

        # Add cache entry
        cache_key = self.client._get_cache_key(endpoint, {"test": "param"})
        self.client.cache[cache_key] = test_data
        self.client.cache_expiry[cache_key] = datetime.now().replace(
            year=9999
        )  # Far future

        # Even though we add a failing response, it shouldn't be called
        responses.add(responses.GET, url, status=500)

        # Make request (should use cache)
        result = self.client._make_request(endpoint, {"test": "param"})

        # Check result
        assert result == test_data
        assert len(responses.calls) == 0  # No API call made


# Test the OpenWeatherMapClient class
class TestOpenWeatherMapClient:
    def setup_method(self):
        self.client = OpenWeatherMapClient(api_key="test_key", cache_enabled=False)

    @responses.activate
    def test_get_current_weather(self):
        """Test getting current weather."""
        lat, lon = 40.0, -111.0
        test_data = {"weather": [{"description": "light snow"}], "main": {"temp": 30.0}}

        # Mock response
        responses.add(
            responses.GET, f"{self.client.base_url}/weather", json=test_data, status=200
        )

        # Get current weather
        result = self.client.get_current_weather(lat, lon)

        # Check result
        assert result == test_data

        # Check request parameters
        assert len(responses.calls) == 1
        assert f"lat={lat}" in responses.calls[0].request.url
        assert f"lon={lon}" in responses.calls[0].request.url
        assert "units=imperial" in responses.calls[0].request.url
        assert f"appid={self.client.api_key}" in responses.calls[0].request.url

    @responses.activate
    def test_get_one_call_data(self):
        """Test getting one call data."""
        lat, lon = 40.0, -111.0
        test_data = {
            "current": {"temp": 30.0, "weather": [{"description": "light snow"}]},
            "daily": [{"snow": 5.0}, {"snow": 2.5}],
        }

        # Mock response
        responses.add(
            responses.GET, f"{self.client.base_url}/onecall", json=test_data, status=200
        )

        # Get one call data
        result = self.client.get_one_call_data(lat, lon)

        # Check result
        assert result == test_data

        # Check request parameters
        assert len(responses.calls) == 1
        assert f"lat={lat}" in responses.calls[0].request.url
        assert f"lon={lon}" in responses.calls[0].request.url
        assert "exclude=minutely%2Chourly" in responses.calls[0].request.url

    @responses.activate
    def test_get_snow_data(self):
        """Test getting snow data."""
        lat, lon = 40.0, -111.0

        # Mock current weather data
        current_weather_data = {
            "main": {"temp": 30.0},
            "weather": [{"description": "light snow"}],
            "snow": {"1h": 2.0},  # 2 inches of snow in the last hour
        }

        # Mock forecast data
        forecast_data = {
            "list": [
                {"dt": 1679432400, "snow": {"3h": 1.5}, "main": {"temp": 28.0}},
                {"dt": 1679443200, "snow": {"3h": 1.0}, "main": {"temp": 29.0}},
                {"dt": 1679454000, "snow": {"3h": 0.5}, "main": {"temp": 30.0}},
                {"dt": 1679464800, "snow": {"3h": 0.0}, "main": {"temp": 31.0}},
                {"dt": 1679475600, "snow": {"3h": 0.0}, "main": {"temp": 32.0}},
                {"dt": 1679486400, "snow": {"3h": 0.0}, "main": {"temp": 33.0}},
                {"dt": 1679497200, "snow": {"3h": 0.0}, "main": {"temp": 34.0}},
                {"dt": 1679508000, "snow": {"3h": 0.0}, "main": {"temp": 35.0}},
            ]
        }

        # Mock responses for both endpoints
        responses.add(
            responses.GET,
            f"{self.client.base_url}/weather",
            json=current_weather_data,
            status=200,
        )

        responses.add(
            responses.GET,
            f"{self.client.base_url}/forecast",
            json=forecast_data,
            status=200,
        )

        # Get snow data
        result = self.client.get_snow_data(lat, lon)

        # Check result
        assert result["current_snow"] == 2.0  # Current snow from weather endpoint
        assert result["forecast_snow"] == 3.0  # Sum of forecast snow (1.5 + 1.0 + 0.5)
        assert result["current_temp"] == 30.0  # Temperature from current weather
        assert result["conditions"] == "light snow"
        assert "timestamp" in result
        assert "OpenWeatherMap" in result["source"]

        # Check that both endpoints were called
        assert len(responses.calls) == 2
        assert "/weather" in responses.calls[0].request.url
        assert "/forecast" in responses.calls[1].request.url


# Test the WeatherApiClient class
class TestWeatherApiClient:
    def setup_method(self):
        self.client = WeatherApiClient(api_key="test_key", cache_enabled=False)

    @responses.activate
    def test_get_current_weather(self):
        """Test getting current weather."""
        lat, lon = 40.0, -111.0
        test_data = {"current": {"temp_f": 30.0, "condition": {"text": "Light snow"}}}

        # Mock response
        responses.add(
            responses.GET,
            f"{self.client.base_url}/current.json",
            json=test_data,
            status=200,
        )

        # Get current weather
        result = self.client.get_current_weather(lat, lon)

        # Check result
        assert result == test_data

        # Check request parameters - use %2C for comma in URL-encoded format
        assert len(responses.calls) == 1
        assert f"q={lat}%2C{lon}" in responses.calls[0].request.url
        assert f"key={self.client.api_key}" in responses.calls[0].request.url

    @responses.activate
    def test_get_forecast(self):
        """Test getting forecast data."""
        lat, lon = 40.0, -111.0
        test_data = {
            "current": {"temp_f": 30.0, "condition": {"text": "Light snow"}},
            "forecast": {"forecastday": [{"day": {"totalsnow_cm": 12.7}}]},
        }

        # Mock response
        responses.add(
            responses.GET,
            f"{self.client.base_url}/forecast.json",
            json=test_data,
            status=200,
        )

        # Get forecast data
        result = self.client.get_forecast(lat, lon, days=1)

        # Check result
        assert result == test_data

        # Check request parameters - use %2C for comma in URL-encoded format
        assert len(responses.calls) == 1
        assert f"q={lat}%2C{lon}" in responses.calls[0].request.url
        assert "days=1" in responses.calls[0].request.url

    @responses.activate
    def test_get_snow_data(self):
        """Test getting snow data."""
        lat, lon = 40.0, -111.0
        test_data = {
            "current": {"temp_f": 30.0, "condition": {"text": "Light snow"}},
            "forecast": {"forecastday": [{"day": {"totalsnow_cm": 12.7}}]},
        }

        # Mock response
        responses.add(
            responses.GET,
            f"{self.client.base_url}/forecast.json",
            json=test_data,
            status=200,
        )

        # Get snow data
        result = self.client.get_snow_data(lat, lon)

        # Check result
        assert result["snow_cm"] == 12.7
        assert round(result["snow_inches"], 1) == 5.0  # 12.7cm ≈ 5.0 inches
        assert result["current_temp"] == 30.0
        assert result["conditions"] == "Light snow"
        assert "timestamp" in result
        assert result["source"] == "WeatherAPI.com"


# Test the helper functions
class TestHelperFunctions:
    @patch("src.weather.client.OpenWeatherMapClient")
    def test_get_resort_snow_data(self, mock_client_class):
        """Test the get_resort_snow_data helper function."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_snow_data.return_value = {
            "current_snow": 5.0,
            "forecast_snow": 2.5,
            "current_temp": 30.0,
            "conditions": "light snow",
            "timestamp": "2025-03-21T12:34:56",
            "source": "OpenWeatherMap (Free API)",
        }

        # Call function
        result = get_resort_snow_data("Test Resort", 40.0, -111.0)

        # Check result
        assert result["resort"] == "Test Resort"
        assert result["current_snow"] == 5.0
        assert result["forecast_snow"] == 2.5
        assert "OpenWeatherMap" in result["source"]

        # Verify mock called with correct parameters
        mock_client.get_snow_data.assert_called_once_with(40.0, -111.0)

    @patch("src.weather.client.WeatherApiClient")
    @patch("time.sleep")
    def test_verify_with_secondary_source_success(self, mock_sleep, mock_client_class):
        """Test successful verification with secondary source."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_snow_data.return_value = {
            "snow_cm": 12.7,
            "snow_inches": 5.0,
            "current_temp": 30.0,
            "conditions": "Light snow",
            "timestamp": "2025-03-21T12:34:56",
            "source": "WeatherAPI.com",
        }

        # Call function
        is_verified, data = verify_with_secondary_source(
            "Test Resort", 40.0, -111.0, 5.0  # Primary snow amount matches secondary
        )

        # Check result
        assert is_verified is True
        assert data["resort"] == "Test Resort"
        assert data["snow_inches"] == 5.0

        # Verify mocks called correctly
        mock_sleep.assert_called_once()
        mock_client.get_snow_data.assert_called_once_with(40.0, -111.0)

    @patch("src.weather.client.WeatherApiClient")
    @patch("time.sleep")
    def test_verify_with_secondary_source_failure(self, mock_sleep, mock_client_class):
        """Test failed verification with secondary source."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_snow_data.return_value = {
            "snow_cm": 25.4,  # 10 inches, well above verification threshold
            "snow_inches": 10.0,
            "current_temp": 30.0,
            "conditions": "Heavy snow",
            "timestamp": "2025-03-21T12:34:56",
            "source": "WeatherAPI.com",
        }

        # Call function
        is_verified, data = verify_with_secondary_source(
            "Test Resort",
            40.0,
            -111.0,
            5.0,  # Primary: 5", Secondary: 10" - doesn't verify
        )

        # Check result
        assert is_verified is False
        assert data["resort"] == "Test Resort"
        assert data["snow_inches"] == 10.0

        # Verify mocks called correctly
        mock_sleep.assert_called_once()
        mock_client.get_snow_data.assert_called_once_with(40.0, -111.0)

    @patch("src.weather.client.WeatherApiClient")
    @patch("time.sleep")
    def test_verify_with_secondary_source_error(self, mock_sleep, mock_client_class):
        """Test error handling in verification function."""
        # Setup mock to raise an exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_snow_data.side_effect = Exception("API error")

        # Call function
        is_verified, data = verify_with_secondary_source(
            "Test Resort", 40.0, -111.0, 5.0
        )

        # Check result
        assert is_verified is False
        assert data is None

        # Verify mocks called correctly
        mock_sleep.assert_called_once()
        mock_client.get_snow_data.assert_called_once_with(40.0, -111.0)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
