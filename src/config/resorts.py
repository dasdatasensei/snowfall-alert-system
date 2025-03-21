"""
Resort configuration for the Snowfall Alert System.

This module defines the ski resorts to be monitored, including their names,
coordinates, and additional metadata.
"""

# Ski resort data near Park City, Utah
RESORTS = {
    "Park City Mountain": {
        "coordinates": (40.6514, -111.5080),
        "elevation": 10000,  # Base elevation in feet
        "website": "https://www.parkcitymountain.com",
        "region": "Park City",
        "type": "Alpine",
        "vertical_drop": 3200,  # in feet
    },
    "Deer Valley": {
        "coordinates": (40.6374, -111.4783),
        "elevation": 8100,
        "website": "https://www.deervalley.com",
        "region": "Park City",
        "type": "Alpine (Ski Only)",
        "vertical_drop": 3000,
    },
    "Snowbird": {
        "coordinates": (40.5830, -111.6556),
        "elevation": 7760,
        "website": "https://www.snowbird.com",
        "region": "Little Cottonwood Canyon",
        "type": "Alpine",
        "vertical_drop": 3240,
    },
    "Alta": {
        "coordinates": (40.5884, -111.6387),
        "elevation": 8530,
        "website": "https://www.alta.com",
        "region": "Little Cottonwood Canyon",
        "type": "Alpine (Ski Only)",
        "vertical_drop": 2538,
    },
    "Brighton": {
        "coordinates": (40.5977, -111.5836),
        "elevation": 8755,
        "website": "https://www.brightonresort.com",
        "region": "Big Cottonwood Canyon",
        "type": "Alpine",
        "vertical_drop": 1875,
    },
    "Solitude": {
        "coordinates": (40.6199, -111.5919),
        "elevation": 8755,
        "website": "https://www.solitudemountain.com",
        "region": "Big Cottonwood Canyon",
        "type": "Alpine",
        "vertical_drop": 2494,
    },
    "Snowbasin": {
        "coordinates": (41.2160, -111.8572),
        "elevation": 6400,
        "website": "https://www.snowbasin.com",
        "region": "Ogden",
        "type": "Alpine",
        "vertical_drop": 3000,
    },
    "Powder Mountain": {
        "coordinates": (41.3803, -111.7803),
        "elevation": 8900,
        "website": "https://www.powdermountain.com",
        "region": "Ogden",
        "type": "Alpine",
        "vertical_drop": 2522,
    },
    "Sundance": {
        "coordinates": (40.3924, -111.5786),
        "elevation": 6100,
        "website": "https://www.sundanceresort.com",
        "region": "Provo",
        "type": "Alpine",
        "vertical_drop": 2150,
    },
    "Woodward Park City": {
        "coordinates": (40.7560, -111.5763),
        "elevation": 6800,
        "website": "https://www.woodwardparkcity.com",
        "region": "Park City",
        "type": "Action Sports",
        "vertical_drop": 400,
    },
}


# Helper function to get just the coordinates for backward compatibility
def get_resort_coordinates():
    """
    Get just the coordinates for each resort.

    Returns:
        Dictionary mapping resort names to (lat, lon) coordinates
    """
    return {name: data["coordinates"] for name, data in RESORTS.items()}


# Legacy support for existing code that expects the old format
RESORT_COORDINATES = get_resort_coordinates()
