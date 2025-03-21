#!/usr/bin/env python3
"""
Local development runner for the Snowfall Alert System.

This module provides a way to run the Lambda function locally for development
and testing purposes without deploying to AWS.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv
from lambda_function import lambda_handler
from utils.logging import get_logger

# Set up logging
logger = get_logger(__name__)


def create_mock_event() -> Dict[str, Any]:
    """
    Create a mock CloudWatch event similar to what would trigger the Lambda.

    Returns:
        Dict containing a mock event payload
    """
    return {
        "version": "0",
        "id": "mock-event-id",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "account": "123456789012",
        "time": datetime.utcnow().isoformat() + "Z",
        "region": "us-west-2",
        "resources": [
            "arn:aws:events:us-west-2:123456789012:rule/SnowfallAlertTrigger"
        ],
        "detail": {},
    }


def create_mock_context() -> object:
    """
    Create a mock AWS Lambda context object.

    Returns:
        A simple object with Lambda context attributes
    """

    class MockContext:
        def __init__(self):
            self.function_name = "SnowfallAlertFunction"
            self.function_version = "$LATEST"
            self.invoked_function_arn = (
                "arn:aws:lambda:us-west-2:123456789012:function:SnowfallAlertFunction"
            )
            self.memory_limit_in_mb = 128
            self.aws_request_id = "mock-request-id"
            self.log_group_name = "/aws/lambda/SnowfallAlertFunction"
            self.log_stream_name = f"2025/03/21/[$LATEST]{hex(int(time.time()))}"
            self.identity = None
            self.client_context = None

        def get_remaining_time_in_millis(self):
            return 30000  # 30 seconds

    return MockContext()


def main():
    """
    Main entry point for local development.

    Loads environment variables, creates mock AWS event and context,
    then executes the Lambda handler.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Check if required environment variables are set
    from config import validate_config

    missing_configs = validate_config()
    if missing_configs:
        logger.error(f"Missing required configuration: {', '.join(missing_configs)}")
        logger.error("Please update your .env file with the required values")
        return

    # Create mock AWS Lambda event and context
    event = create_mock_event()
    context = create_mock_context()

    # If USE_MOCK_DATA is set, enable development mode
    if os.environ.get("USE_MOCK_DATA", "false").lower() == "true":
        logger.info("Running in development mode with mock data")
    else:
        logger.info("Running with real API calls")

    logger.info("Executing Lambda function locally")

    # Execute the Lambda handler
    try:
        response = lambda_handler(event, context)

        # Pretty print the response
        logger.info("Lambda execution result:")
        print(json.dumps(json.loads(response.get("body", "{}")), indent=2))

        logger.info(f"Status code: {response.get('statusCode')}")
    except Exception as e:
        logger.exception("Error executing Lambda function locally")


if __name__ == "__main__":
    main()
