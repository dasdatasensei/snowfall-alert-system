"""
Integration tests for the Snowfall Alert System.

This module contains integration tests that verify the system works
as a whole, from data retrieval to alert generation.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.core.processor import SnowfallProcessor
from src.config.resort_config import get_resort_by_region


@pytest.mark.integration
@patch("src.weather.client.requests.Session.get")
def test_end_to_end_flow(mock_requests):
    """Test the end-to-end flow from data retrieval to alert generation."""
    # Skip this test if environment variable is set
    if os.environ.get("SKIP_INTEGRATION_TESTS"):
        pytest.skip("Integration tests disabled by environment variable")

    # Mock the API responses
    def mock_api_response(*args, **kwargs):
        url = args[0] if args else kwargs.get("url", "")

        # Create a mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # OpenWeatherMap current weather endpoint
        if "openweathermap" in url and "weather" in url:
            mock_response.json.return_value = {
                "main": {"temp": 28.4},
                "weather": [{"description": "heavy snow"}],
                "snow": {"1h": 12.5},  # 12.5 inches of snow in the last hour
            }

        # OpenWeatherMap forecast endpoint
        elif "openweathermap" in url and "forecast" in url:
            mock_response.json.return_value = {
                "list": [
                    {"dt": 1679432400, "snow": {"3h": 1.2}, "main": {"temp": 28.0}},
                    {"dt": 1679443200, "snow": {"3h": 0.8}, "main": {"temp": 29.0}},
                    {"dt": 1679454000, "snow": {"3h": 0.7}, "main": {"temp": 30.0}},
                    {"dt": 1679464800, "snow": {"3h": 0.5}, "main": {"temp": 31.0}},
                    {"dt": 1679475600, "snow": {"3h": 0.0}, "main": {"temp": 32.0}},
                    {"dt": 1679486400, "snow": {"3h": 0.0}, "main": {"temp": 33.0}},
                    {"dt": 1679497200, "snow": {"3h": 0.0}, "main": {"temp": 34.0}},
                    {"dt": 1679508000, "snow": {"3h": 0.0}, "main": {"temp": 35.0}},
                ]
            }

        # WeatherAPI.com forecast endpoint
        elif "weatherapi.com" in url and "forecast" in url:
            mock_response.json.return_value = {
                "current": {"temp_f": 28.6, "condition": {"text": "Heavy snow"}},
                "forecast": {
                    "forecastday": [{"day": {"totalsnow_cm": 30.0}}]  # ~12 inches
                },
            }

        return mock_response

    # Set up the mock response
    mock_requests.side_effect = mock_api_response

    # Get test resorts
    test_resorts = get_resort_by_region("Park City")
    assert len(test_resorts) > 0, "No test resorts found"

    # Create the processor
    processor = SnowfallProcessor(test_resorts)

    # Process all resorts
    results = processor.process_all_resorts()

    # Verify the results
    assert results["resorts_processed"] > 0, "No resorts were processed"
    assert results["alerts_triggered"] > 0, "No alerts were triggered"
    assert len(results["results"]) > 0, "No results were returned"

    # Check that at least one resort triggered an alert
    alert_triggered = False
    for resort_result in results["results"].values():
        if resort_result.get("alert_triggered", False):
            alert_triggered = True
            break

    assert alert_triggered, "No alerts were triggered for any resort"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
