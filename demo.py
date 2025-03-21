#!/usr/bin/env python3
"""
Demo script for the Snowfall Alert System.
This script runs the Snowfall Alert System with real API calls to demonstrate its functionality.
"""

import os
import json
from datetime import datetime
import requests

# Import the system components
from src.core.processor import SnowfallProcessor
from src.config.resort_config import get_enabled_resorts, get_resort_by_region
from src.utils.logging import get_logger
from src.lambda_function import send_snow_alert, send_status_update
from src.config.settings import OPENWEATHER_API_KEY, WEATHERAPI_KEY, SLACK_WEBHOOK_URL

# Set up logging
logger = get_logger(__name__)


def print_section(title):
    """Print a section title for better readability."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def test_api_keys():
    """Test the API keys to verify they're working correctly."""
    print_section("API Key Verification")

    # Test OpenWeatherMap API key
    openweather_url = f"https://api.openweathermap.org/data/2.5/weather?q=Salt+Lake+City&appid={OPENWEATHER_API_KEY}"
    print(
        f"Testing OpenWeatherMap API key: {OPENWEATHER_API_KEY[:4]}...{OPENWEATHER_API_KEY[-4:]}"
    )

    try:
        response = requests.get(openweather_url)
        if response.status_code == 200:
            print("✅ OpenWeatherMap API key is valid!")
        else:
            print(
                f"❌ OpenWeatherMap API key error: {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"❌ Error testing OpenWeatherMap API: {str(e)}")

    # Test WeatherAPI key
    weatherapi_url = f"https://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q=Salt+Lake+City"
    print(f"Testing WeatherAPI key: {WEATHERAPI_KEY[:4]}...{WEATHERAPI_KEY[-4:]}")

    try:
        response = requests.get(weatherapi_url)
        if response.status_code == 200:
            print("✅ WeatherAPI key is valid!")
        else:
            print(f"❌ WeatherAPI key error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error testing WeatherAPI: {str(e)}")

    print("\nMake sure both API keys are valid before continuing.")


def test_slack_notifications():
    """Test Slack notifications functionality."""
    print_section("Testing Slack Notifications")

    # First, verify Slack webhook URL
    print(
        f"Slack Webhook URL configured: {SLACK_WEBHOOK_URL[:20]}...{SLACK_WEBHOOK_URL[-10:]}"
    )

    # Create example data for a heavy snowfall
    test_resort = {
        "name": "Park City Mountain",
        "region": "Park City",
        "coordinates": (40.6514, -111.508),
    }

    snow_data = {
        "current_snow": 9.5,  # Current snowfall in inches
        "forecast_snow": 3.2,  # Forecast additional snowfall
        "current_temp": 28.4,  # Current temperature
        "conditions": "Heavy snow",  # Weather conditions
        "source": "OpenWeatherMap (Test)",
    }

    # Create test alert data
    alert_data = {
        "resort_name": test_resort["name"],
        "region": test_resort["region"],
        "snow_amount": snow_data["current_snow"],
        "forecast_amount": snow_data["forecast_snow"],
        "temperature": snow_data["current_temp"],
        "conditions": snow_data["conditions"],
        "alert_category": "moderate",
        "timestamp": datetime.now().isoformat(),
        "verified": True,
    }

    print("Sending test alert notification to Slack...")
    success = send_snow_alert(alert_data=alert_data, test=True)

    if success:
        print("✅ Snow alert notification sent successfully!")
    else:
        print("❌ Failed to send snow alert notification.")

    print("\nSending system status update to monitoring channel...")
    status_data = {
        "resorts_processed": 3,
        "alerts_triggered": 1,
        "processing_time_ms": 450,
        "errors": 0,
    }

    success = send_status_update(status_data=status_data, test=True)

    if success:
        print("✅ Status update sent successfully!")
    else:
        print("❌ Failed to send status update.")


def main():
    """Run the demo of the Snowfall Alert System."""
    print_section("Snowfall Alert System Demo")
    print("This demo will run the Snowfall Alert System with real API calls.")

    # Test API keys first
    test_api_keys()

    # Step 1: Display resort configuration
    print_section("Resort Configuration")

    # For demo purposes, use a subset of resorts in Park City
    resorts = get_resort_by_region("Park City")
    print(f"Monitoring {len(resorts)} resorts:")

    for name, data in resorts.items():
        print(f"- {name}: {data['region']} (Coordinates: {data['coordinates']})")

    # Step 2: Create and run the processor
    print_section("Processing Snowfall Data")
    print("Fetching real-time weather data from APIs...")
    print("This may take a minute or two to complete.")

    # Create the processor and process all resorts
    processor = SnowfallProcessor(resorts)
    results = processor.process_all_resorts()

    # Step 3: Display results
    print_section("Processing Results")

    print(f"Resorts processed: {results['resorts_processed']}")
    print(f"Alerts triggered: {results['alerts_triggered']}")
    print("\nDetailed results:")

    for resort_name, result in results["results"].items():
        alert_status = (
            "✅ ALERT TRIGGERED" if result.get("alert_triggered") else "❌ No alert"
        )
        category = result.get("alert_category", "none")

        print(f"\n{resort_name} - {alert_status} (Category: {category})")

        if "primary_data" in result:
            snow = result["primary_data"].get("current_snow", 0)
            forecast = result["primary_data"].get("forecast_snow", 0)
            temp = result["primary_data"].get("current_temp", "N/A")

            print(f"  Current Snow: {snow} inches")
            print(f"  Forecast Snow: {forecast} inches")
            print(f"  Temperature: {temp}°F")

        if result.get("verified"):
            print("  ✓ Verified by secondary source")

    # Step 4: Test Slack notifications
    test_slack_notifications()

    print_section("Demo Complete")
    print(
        "In a real deployment, alerts would be sent to Slack and potentially other notification channels."
    )
    print("You can configure these channels in the .env file.")


if __name__ == "__main__":
    main()
