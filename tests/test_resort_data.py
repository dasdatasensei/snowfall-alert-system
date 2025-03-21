#!/usr/bin/env python
"""
Test script for resort data structure and processing.

This script demonstrates how to use the enhanced resort data structure
and tests the core functionality of the system.
"""

import sys
import os
import json
from pprint import pprint

# Add project root to path to allow importing
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.config.resorts import RESORTS
from src.config.resort_config import get_enabled_resorts, get_resort_by_region
from src.utils.resort_validator import validate_all_resorts
from src.core.processor import SnowfallProcessor
from src.utils.logging import get_logger

logger = get_logger(__name__)


def main():
    """
    Main function for the test script.
    """
    print("\n=== Snowfall Alert System: Resort Data Test ===\n")

    # Display available resorts
    print(f"Total Resorts: {len(RESORTS)}")
    for name, data in RESORTS.items():
        region = data.get("region", "Unknown")
        coords = data.get("coordinates", (0, 0))
        print(f"- {name} ({region}): {coords[0]:.4f}, {coords[1]:.4f}")

    # Get resorts by region
    print("\n=== Resorts by Region ===\n")
    regions = set(data.get("region", "Unknown") for data in RESORTS.values())

    for region in sorted(regions):
        regional_resorts = get_resort_by_region(region)
        print(f"\n{region} ({len(regional_resorts)} resorts):")
        for name, data in regional_resorts.items():
            elevation = data.get("elevation", "N/A")
            print(f"- {name} (Elevation: {elevation} ft)")

    # Validate resort data
    print("\n=== Resort Data Validation ===\n")
    validation_errors = validate_all_resorts(RESORTS)

    if validation_errors:
        print(f"Found {len(validation_errors)} resorts with validation issues:")
        for resort, errors in validation_errors.items():
            print(f"- {resort}:")
            for error in errors:
                print(f"  • {error}")
    else:
        print("All resort data passed validation!")

    # Test SnowfallProcessor with updated structure
    print("\n=== Testing SnowfallProcessor ===\n")

    # Use just one resort for quick testing
    test_resort_name = list(RESORTS.keys())[0]
    test_resort_data = RESORTS[test_resort_name]
    test_resorts = {test_resort_name: test_resort_data}

    print(f"Testing with resort: {test_resort_name}")

    # Create processor with just the test resort
    processor = SnowfallProcessor(test_resorts)

    # Instead of actually calling APIs, we'll just demonstrate the structure
    print("\nProcessor would process the following resort data:")
    pprint(test_resort_data)

    print("\n=== Integration with Lambda Handler ===")
    print("The lambda_handler now expects the new resort data structure and will:")
    print("1. Get enabled resorts using get_enabled_resorts()")
    print("2. Pass the resort data to SnowfallProcessor")
    print("3. Include resort metadata in Slack notifications")
    print("4. Group resort conditions by region in status updates")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
