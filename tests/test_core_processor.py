"""
Tests for the core processing logic.

This module contains tests for the SnowfallProcessor class and related functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.core.processor import SnowfallProcessor


class TestSnowfallProcessor:
    """Tests for the SnowfallProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_resorts = {
            "Test Resort 1": (40.0, -111.0),
            "Test Resort 2": (41.0, -112.0),
        }
        self.processor = SnowfallProcessor(self.test_resorts)

    def test_determine_alert_category(self):
        """Test determining alert category based on snow amount."""
        # Test light snow threshold
        assert self.processor.determine_alert_category(1.0) == "none"
        assert self.processor.determine_alert_category(2.0) == "light"
        assert self.processor.determine_alert_category(5.0) == "light"

        # Test moderate snow threshold
        assert self.processor.determine_alert_category(6.0) == "moderate"
        assert self.processor.determine_alert_category(10.0) == "moderate"

        # Test heavy snow threshold
        assert self.processor.determine_alert_category(12.0) == "heavy"
        assert self.processor.determine_alert_category(20.0) == "heavy"

    def test_calculate_time_window_data(self):
        """Test calculation of time window data."""
        # Test with basic current data
        current_data = {"current_snow": 5.0, "forecast_snow": 3.0}

        result = self.processor.calculate_time_window_data(current_data)

        assert result["current_24h"] == 5.0
        assert result["forecast_24h"] == 3.0
        assert result["total_48h"] == 8.0

        # Test with missing data
        incomplete_data = {"current_snow": 5.0}

        result = self.processor.calculate_time_window_data(incomplete_data)

        assert result["current_24h"] == 5.0
        assert result["forecast_24h"] == 0
        assert result["total_48h"] == 5.0

    def test_is_in_cooldown(self):
        """Test cooldown period checking."""
        resort = "Test Resort"
        category = "light"

        # Resort not in last_alerts yet
        assert not self.processor.is_in_cooldown(resort, category)

        # Add resort but not category
        self.processor.last_alerts[resort] = {}
        assert not self.processor.is_in_cooldown(resort, category)

        # Add an alert time for the resort/category in the past (beyond cooldown)
        past_time = datetime.now() - timedelta(hours=24)
        self.processor.last_alerts[resort][category] = past_time
        assert not self.processor.is_in_cooldown(resort, category)

        # Add a recent alert time (within cooldown)
        recent_time = datetime.now() - timedelta(hours=1)
        self.processor.last_alerts[resort][category] = recent_time
        assert self.processor.is_in_cooldown(resort, category)

    def test_update_last_alert_time(self):
        """Test updating the last alert time."""
        resort = "Test Resort"
        category = "moderate"

        # Resort not in last_alerts initially
        assert resort not in self.processor.last_alerts

        # Update the last alert time
        self.processor.update_last_alert_time(resort, category)

        # Check that it was updated
        assert resort in self.processor.last_alerts
        assert category in self.processor.last_alerts[resort]
        assert isinstance(self.processor.last_alerts[resort][category], datetime)

        # Time should be recent
        time_diff = datetime.now() - self.processor.last_alerts[resort][category]
        assert time_diff.total_seconds() < 1.0  # Less than 1 second ago

    def test_should_trigger_alert_unverified(self):
        """Test alert triggering logic with unverified data."""
        resort = "Test Resort"

        # Snow data above threshold but not verified
        snow_data = {"current_24h": 5.0, "forecast_24h": 3.0, "total_48h": 8.0}

        should_alert, category = self.processor.should_trigger_alert(
            resort, snow_data, is_verified=False
        )

        # Should not trigger alert if not verified
        assert not should_alert
        assert category is None

    def test_should_trigger_alert_verified(self):
        """Test alert triggering logic with verified data."""
        resort = "Test Resort"

        # Snow data above threshold and verified
        snow_data = {"current_24h": 5.0, "forecast_24h": 3.0, "total_48h": 8.0}

        should_alert, category = self.processor.should_trigger_alert(
            resort, snow_data, is_verified=True
        )

        # Should trigger alert
        assert should_alert
        assert category == "light"

        # Update last alert time to simulate recent alert
        self.processor.update_last_alert_time(resort, "light")

        # Try triggering again - should be in cooldown
        should_alert, category = self.processor.should_trigger_alert(
            resort, snow_data, is_verified=True
        )

        # Should not trigger due to cooldown
        assert not should_alert
        assert category is None

    @patch("src.core.processor.get_resort_snow_data")
    @patch("src.core.processor.verify_with_secondary_source")
    def test_process_resort_no_alert(self, mock_verify, mock_get_data):
        """Test processing a resort with no alert triggered."""
        resort = "Test Resort"
        coordinates = (40.0, -111.0)

        # Mock the snow data below threshold
        mock_get_data.return_value = {
            "resort": resort,
            "current_snow": 1.0,  # Below light threshold
            "forecast_snow": 0.5,
            "current_temp": 30.0,
            "conditions": "Partly cloudy",
            "timestamp": datetime.now().isoformat(),
            "source": "OpenWeatherMap",
        }

        # Process the resort
        result = self.processor.process_resort(resort, coordinates)

        # Should not have triggered an alert
        assert not result["alert_triggered"]
        assert result["alert_category"] is None

        # Verify should not have been called (snow below threshold)
        mock_verify.assert_not_called()

    @patch("src.core.processor.get_resort_snow_data")
    @patch("src.core.processor.verify_with_secondary_source")
    def test_process_resort_with_alert(self, mock_verify, mock_get_data):
        """Test processing a resort with alert triggered."""
        resort = "Test Resort"
        coordinates = (40.0, -111.0)
        # Create a properly structured resort data dictionary with coordinates
        resort_data = {
            "coordinates": coordinates,
            "elevation": 9000,
            "region": "Test Region",
        }

        # Mock the snow data above threshold
        mock_get_data.return_value = {
            "resort": resort,
            "current_snow": 8.0,  # Above moderate threshold
            "forecast_snow": 2.0,
            "current_temp": 28.0,
            "conditions": "Snow",
            "timestamp": datetime.now().isoformat(),
            "source": "OpenWeatherMap",
        }

        # Mock the verification (success)
        mock_verify.return_value = (
            True,
            {
                "resort": resort,
                "snow_cm": 20.32,  # ~8 inches
                "snow_inches": 8.0,
                "current_temp": 28.0,
                "conditions": "Snow",
                "timestamp": datetime.now().isoformat(),
                "source": "WeatherAPI.com",
            },
        )

        # Process the resort
        result = self.processor.process_resort(resort, resort_data)

        # Should have triggered an alert
        assert result["alert_triggered"]
        assert result["alert_category"] == "moderate"
        assert result["verified"]

        # Verify should have been called
        mock_verify.assert_called_once()

    @patch("src.core.processor.get_resort_snow_data")
    def test_process_resort_error(self, mock_get_data):
        """Test processing a resort with an error."""
        resort = "Test Resort"
        coordinates = (40.0, -111.0)
        # Create a properly structured resort data dictionary with coordinates
        resort_data = {
            "coordinates": coordinates,
            "elevation": 9000,
            "region": "Test Region",
        }

        # Mock the snow data retrieval to raise an exception
        mock_get_data.side_effect = Exception("API error")

        # Process the resort
        result = self.processor.process_resort(resort, resort_data)

        # Should have an error
        assert result["error"] is not None
        assert "API error" in result["error"]
        assert not result["alert_triggered"]

    @patch("src.core.processor.SnowfallProcessor.process_resort")
    def test_process_all_resorts(self, mock_process_resort):
        """Test processing all resorts."""
        # Mock the process_resort method to return different results
        mock_process_resort.side_effect = [
            {
                "resort": "Test Resort 1",
                "alert_triggered": True,
                "alert_category": "light",
                "error": None,
            },
            {
                "resort": "Test Resort 2",
                "alert_triggered": False,
                "alert_category": None,
                "error": "API error",
            },
        ]

        # Process all resorts
        results = self.processor.process_all_resorts()

        # Check summary stats
        assert results["resorts_processed"] == 2
        assert results["alerts_triggered"] == 1
        assert results["errors"] == 1

        # Check individual results
        assert "Test Resort 1" in results["results"]
        assert "Test Resort 2" in results["results"]

        # Verify process_resort was called for each resort
        assert mock_process_resort.call_count == 2


# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])
