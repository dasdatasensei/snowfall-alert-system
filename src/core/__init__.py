"""
Core processing package for the Snowfall Alert System.

This package contains the main business logic for processing snowfall data,
detecting threshold exceedances, and triggering alerts.
"""

from src.core.processor import SnowfallProcessor

__all__ = ["SnowfallProcessor"]
