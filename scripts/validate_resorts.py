#!/usr/bin/env python
"""
Resort validation script for the Snowfall Alert System.

This script validates the resort data and coordinates, displaying
the results in a formatted table.
"""

import sys
import os
import argparse
from datetime import datetime
from tabulate import tabulate

# Add project root to path to allow importing
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.config.resorts import RESORTS
from src.utils.resort_validator import validate_all_resorts
from src.utils.coordinate_validator import validate_all_resort_coordinates
from src.utils.logging import get_logger

logger = get_logger(__name__)


def display_results(resort_validation_results, coordinate_validation_results):
    """
    Display validation results in a formatted table.

    Args:
        resort_validation_results: Results from resort data validation
        coordinate_validation_results: Results from coordinate validation
    """
    # Create a table with the results
    table_data = []

    for resort_name, resort_data in RESORTS.items():
        coord_result = coordinate_validation_results.get(resort_name, {})
        has_resort_errors = resort_name in resort_validation_results

        row = [
            resort_name,
            f"{resort_data.get('coordinates', (None, None))[0]:.4f}, {resort_data.get('coordinates', (None, None))[1]:.4f}",
            resort_data.get("elevation", "N/A"),
            resort_data.get("region", "N/A"),
            "❌" if has_resort_errors else "✅",
            "✅" if coord_result.get("openweathermap_valid", False) else "❌",
            "✅" if coord_result.get("weatherapi_valid", False) else "❌",
            ", ".join(coord_result.get("location_names", {}).values()) or "N/A",
        ]
        table_data.append(row)

    # Display the table
    headers = [
        "Resort",
        "Coordinates",
        "Elevation",
        "Region",
        "Data Valid",
        "OWM Valid",
        "WA Valid",
        "Detected Locations",
    ]

    print("\n=== Snowfall Alert System: Resort Validation Results ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Resorts: {len(RESORTS)}")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Summary
    print("\n=== Summary ===")

    # Resort data validation summary
    if resort_validation_results:
        print(f"\nResort Data Issues ({len(resort_validation_results)} resorts):")
        for resort, errors in resort_validation_results.items():
            print(f"- {resort}:")
            for error in errors:
                print(f"  • {error}")
    else:
        print("\nAll resort data is valid! ✅")

    # Coordinate validation summary
    valid_coords = sum(
        1 for r in coordinate_validation_results.values() if r.get("both_valid", False)
    )
    print(
        f"\nCoordinate Validation: {valid_coords}/{len(RESORTS)} resorts valid with both APIs"
    )

    for resort, result in coordinate_validation_results.items():
        if result.get("errors"):
            print(f"- {resort} coordinate issues:")
            for error in result.get("errors", []):
                print(f"  • {error}")


def main():
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Validate resort data and coordinates")
    parser.add_argument(
        "--skip-coordinates",
        action="store_true",
        help="Skip coordinate validation (faster)",
    )
    parser.add_argument("--resort", help="Validate only a specific resort")
    args = parser.parse_args()

    try:
        # Filter resorts if specified
        resorts_to_validate = RESORTS
        if args.resort:
            if args.resort in RESORTS:
                resorts_to_validate = {args.resort: RESORTS[args.resort]}
                print(f"Validating only resort: {args.resort}")
            else:
                print(f"Error: Resort '{args.resort}' not found in configuration")
                return 1

        # Validate resort data
        print("Validating resort data...")
        resort_validation_results = validate_all_resorts(resorts_to_validate)

        # Validate coordinates (unless skipped)
        coordinate_validation_results = {}
        if not args.skip_coordinates:
            print(
                "Validating coordinates with weather APIs (this may take a moment)..."
            )
            coordinate_validation_results = validate_all_resort_coordinates(
                resorts_to_validate
            )
        else:
            print("Skipping coordinate validation")

        # Display results
        display_results(resort_validation_results, coordinate_validation_results)

        return 0

    except Exception as e:
        logger.exception(f"Error in validation script: {e}")
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
