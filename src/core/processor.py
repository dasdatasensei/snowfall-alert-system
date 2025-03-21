"""
Core processing logic for the Snowfall Alert System.

This module contains the main business logic for processing snowfall data,
detecting threshold exceedances, and triggering alerts.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

from src.utils.logging import get_logger, ExecutionTimer
from src.weather.client import get_resort_snow_data, verify_with_secondary_source
from src.config.settings import (
    THRESHOLD_LIGHT,
    THRESHOLD_MODERATE,
    THRESHOLD_HEAVY,
    VERIFICATION_THRESHOLD,
    ALERT_COOLDOWN_HOURS,
)
from src.config.resort_config import get_enabled_resorts

# Initialize logger
logger = get_logger(__name__)


class SnowfallProcessor:
    """
    Core processor for snowfall data and alert triggering.

    This class handles the main business logic for processing snowfall data,
    including threshold detection, time window calculations, and alert triggering.
    """

    def __init__(self, resorts=None):
        """
        Initialize the processor.

        Args:
            resorts: Optional dictionary of resorts to process.
                    If not provided, enabled resorts will be loaded from configuration.
        """
        self.resorts = resorts if resorts is not None else get_enabled_resorts()
        self.last_alerts = self._load_last_alerts()

    def _load_last_alerts(self) -> Dict[str, Dict[str, datetime]]:
        """
        Load the last alert times for each resort and category.

        In a production system, this would load from a database or file.
        For this implementation, we'll use a simple in-memory approach.

        Returns:
            Dictionary mapping resort names to dictionaries of category -> last alert time
        """
        # In a real implementation, this would load from a persistent store
        return {}

    def _save_last_alerts(self) -> None:
        """
        Save the last alert times for each resort and category.

        In a production system, this would save to a database or file.
        """
        # In a real implementation, this would save to a persistent store
        pass

    def is_in_cooldown(self, resort_name: str, category: str) -> bool:
        """
        Check if a resort is in cooldown period for a specific alert category.
        This prevents sending too many alerts for the same resort in a short period.

        Args:
            resort_name: Name of the resort
            category: Alert category (light, moderate, heavy)

        Returns:
            Boolean indicating if resort is in cooldown
        """
        if resort_name not in self.last_alerts:
            return False

        if category not in self.last_alerts[resort_name]:
            return False

        last_time = self.last_alerts[resort_name][category]
        cooldown_period = timedelta(hours=ALERT_COOLDOWN_HOURS)

        return datetime.now() < last_time + cooldown_period

    def update_last_alert_time(self, resort_name: str, category: str) -> None:
        """
        Update the last alert time for a resort and category.

        Args:
            resort_name: Name of the resort
            category: Alert category (light, moderate, heavy)
        """
        if resort_name not in self.last_alerts:
            self.last_alerts[resort_name] = {}

        self.last_alerts[resort_name][category] = datetime.now()
        self._save_last_alerts()

    def determine_alert_category(self, snow_amount: float) -> str:
        """
        Determine the alert category based on snowfall amount.

        Args:
            snow_amount: Amount of snow in inches

        Returns:
            String category: "light", "moderate", "heavy", or "none"
        """
        if snow_amount >= THRESHOLD_HEAVY:
            return "heavy"
        elif snow_amount >= THRESHOLD_MODERATE:
            return "moderate"
        elif snow_amount >= THRESHOLD_LIGHT:
            return "light"
        else:
            return "none"

    def calculate_time_window_data(
        self,
        current_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate snowfall amounts over different time windows.

        Args:
            current_data: Current snow data for a resort
            historical_data: Optional list of historical data points

        Returns:
            Dictionary with snow amounts for different time windows
        """
        result = {
            "current_24h": current_data.get("current_snow", 0),
            "forecast_24h": current_data.get("forecast_snow", 0),
            "total_48h": current_data.get("current_snow", 0)
            + current_data.get("forecast_snow", 0),
        }

        # If historical data is provided, we could do more sophisticated calculations
        if historical_data:
            # This would combine historical data to get more accurate time windows
            # For this implementation, we'll just use the current data
            pass

        return result

    def should_trigger_alert(
        self, resort_name: str, snow_data: Dict[str, Any], is_verified: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if an alert should be triggered based on snow data.

        Args:
            resort_name: Name of the resort
            snow_data: Processed snow data including time windows
            is_verified: Whether the data has been verified by a secondary source

        Returns:
            Tuple containing:
            - Boolean indicating if alert should be triggered
            - Alert category if triggered, None otherwise
        """
        # Check if data is verified (if needed)
        if snow_data["current_24h"] >= THRESHOLD_LIGHT and not is_verified:
            logger.info(f"Snow data for {resort_name} not verified, skipping alert")
            return False, None

        # Determine alert category
        category = self.determine_alert_category(snow_data["current_24h"])

        # No alert if below threshold
        if category == "none":
            return False, None

        # Check cooldown period to prevent duplicate alerts
        if self.is_in_cooldown(resort_name, category):
            logger.info(
                f"Resort {resort_name} is in cooldown for {category} alerts, skipping"
            )
            return False, None

        # All checks passed, should trigger alert
        return True, category

    def process_resort(
        self, resort_name: str, resort_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a single resort's data.

        Args:
            resort_name: Name of the resort
            resort_data: Resort configuration data

        Returns:
            Processing result including alerts and data
        """
        result = {
            "resort": resort_name,
            "resort_data": resort_data,
            "timestamp": datetime.now().isoformat(),
            "alert_triggered": False,
            "alert_category": None,
            "verified": False,
            "error": None,
        }

        try:
            # Get coordinates from resort data
            if "coordinates" not in resort_data:
                logger.error(f"Resort {resort_name} missing coordinates")
                result["error"] = "Missing coordinates"
                return result

            coordinates = resort_data["coordinates"]
            result["coordinates"] = coordinates

            # Get snow data
            with ExecutionTimer(f"process_{resort_name}", logger):
                # Fetch primary data
                lat, lon = coordinates
                primary_data = get_resort_snow_data(resort_name, lat, lon)
                result["primary_data"] = primary_data

                # Add metadata to the primary data
                primary_data["elevation"] = resort_data.get("elevation")
                primary_data["region"] = resort_data.get("region")

                # Calculate time window data
                time_window_data = self.calculate_time_window_data(primary_data)
                result["time_window_data"] = time_window_data

                # Verify with secondary source if significant snow detected
                is_verified = False
                if time_window_data["current_24h"] >= THRESHOLD_LIGHT:
                    is_verified, secondary_data = verify_with_secondary_source(
                        resort_name, lat, lon, time_window_data["current_24h"]
                    )
                    result["verified"] = is_verified
                    if secondary_data:
                        result["secondary_data"] = secondary_data

                # Determine if alert should be triggered
                should_alert, category = self.should_trigger_alert(
                    resort_name, time_window_data, is_verified
                )

                if should_alert:
                    result["alert_triggered"] = True
                    result["alert_category"] = category
                    # Update last alert time
                    self.update_last_alert_time(resort_name, category)

        except Exception as e:
            logger.exception(f"Error processing resort {resort_name}")
            result["error"] = str(e)

        return result

    def process_all_resorts(self) -> Dict[str, Any]:
        """
        Process all configured resorts.

        Returns:
            Dictionary with processing results for all resorts
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "resorts_processed": 0,
            "alerts_triggered": 0,
            "errors": 0,
            "results": {},
        }

        for resort_name, resort_data in self.resorts.items():
            resort_result = self.process_resort(resort_name, resort_data)
            results["results"][resort_name] = resort_result

            results["resorts_processed"] += 1

            if resort_result.get("alert_triggered", False):
                results["alerts_triggered"] += 1

            if resort_result.get("error"):
                results["errors"] += 1

        return results
