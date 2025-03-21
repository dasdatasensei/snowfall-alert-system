"""
AWS Lambda function handler for the Snowfall Alert System.

This module contains the main entry point for the AWS Lambda function that
checks for new snowfall at configured ski resorts and sends alerts to Slack.
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Any

# Import from our project modules
from src.utils.logging import get_logger, log_lambda_context, ExecutionTimer
from src.core.processor import SnowfallProcessor
from src.config import validate_config
from src.config.resort_config import get_enabled_resorts
from src.config.env_validator import (
    validate_environment_variables,
    check_for_default_values,
)

# Configure the webhooks from environment variables
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
SLACK_MONITORING_WEBHOOK_URL = os.environ.get(
    "SLACK_MONITORING_WEBHOOK_URL", SLACK_WEBHOOK_URL
)

# Initialize logger
logger = get_logger(__name__)


def lambda_handler(event: Dict, context: Any) -> Dict:
    """
    AWS Lambda function handler for the Snowfall Alert System.

    Args:
        event (dict): The event data passed to the Lambda function
        context (object): The runtime information provided by AWS Lambda

    Returns:
        dict: Response containing the execution status and message
    """
    # Log the Lambda invocation with relevant context
    logger.info(
        "Lambda function invoked",
        timestamp=datetime.now().isoformat(),
        event_type=(
            event.get("source", "manual") if isinstance(event, dict) else "unknown"
        ),
    )

    # Log AWS Lambda context information if available
    if context:
        log_lambda_context(logger, context)

    # Validate environment variables
    validate_environment_variables()

    # Check for suspicious default values
    suspicious = check_for_default_values()
    if suspicious:
        logger.warning("The following variables may contain default/example values:")
        for var in suspicious:
            logger.warning(f"  - {var}")

    # Validate configuration
    missing_configs = validate_config()
    if missing_configs:
        logger.warning(
            f"Missing required configuration variables: {', '.join(missing_configs)}"
        )

    # Initialize collections for tracking
    alerts_sent = []
    errors = []

    # Use the execution timer as a context manager to measure overall execution time
    with ExecutionTimer("lambda_execution", logger):
        try:
            # Get enabled resorts
            enabled_resorts = get_enabled_resorts()
            logger.info(f"Processing {len(enabled_resorts)} enabled resorts")

            # Create and run the snowfall processor
            processor = SnowfallProcessor(enabled_resorts)
            results = processor.process_all_resorts()

            # Process results and send alerts
            for resort_name, resort_result in results["results"].items():
                if resort_result.get("error"):
                    errors.append(
                        f"Error processing {resort_name}: {resort_result['error']}"
                    )

                if resort_result.get("alert_triggered", False):
                    # Send alert for this resort
                    category = resort_result["alert_category"]
                    snow_amount = resort_result["time_window_data"]["current_24h"]

                    # Get snow data from the processing result
                    snow_data = resort_result.get("primary_data", {})

                    # Send the alert to Slack
                    success = send_snow_alert(
                        resort_name,
                        snow_data,
                        category,
                        resort_result.get("resort_data", {}),
                    )

                    if success:
                        alerts_sent.append(
                            {
                                "resort": resort_name,
                                "snow_amount": snow_amount,
                                "category": category,
                            }
                        )

            # Send status update to monitoring channel
            send_status_update(results["results"], errors, alerts_sent)

            logger.info(
                "Processing completed successfully",
                resorts_processed=results["resorts_processed"],
                alerts_triggered=results["alerts_triggered"],
                alerts_sent=len(alerts_sent),
                errors=len(errors),
            )

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "Snowfall Alert System execution completed successfully",
                        "timestamp": datetime.now().isoformat(),
                        "resorts_processed": results["resorts_processed"],
                        "alerts_triggered": results["alerts_triggered"],
                        "alerts_sent": len(alerts_sent),
                        "errors": len(errors),
                    }
                ),
            }

        except Exception as e:
            # Log the exception with full details
            logger.exception(
                "Error in lambda_handler",
                error_type=type(e).__name__,
                error_message=str(e),
            )

            # Try to send a status update even if there was an error
            try:
                send_status_update({}, [str(e)], [])
            except Exception as status_error:
                logger.exception("Failed to send error status update")

            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "message": f"Error: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            }


def send_snow_alert(
    alert_data: Dict = None,
    resort_name: str = None,
    snow_data: Dict = None,
    category: str = None,
    resort_metadata: Dict = None,
    test: bool = False,
) -> bool:
    """
    Send a Slack notification for significant snowfall.

    Args:
        alert_data: Consolidated alert data (used for testing)
        resort_name: Name of the resort with significant snow
        snow_data: Dictionary containing snow information
        category: Alert category ("light", "moderate", "heavy")
        resort_metadata: Optional additional resort metadata
        test: Whether this is a test notification

    Returns:
        Boolean indicating if the alert was sent successfully
    """
    # Check if webhook URL is available
    if not SLACK_WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL environment variable not set")
        return False

    # For test mode, use alert_data if provided
    if test and alert_data:
        resort_name = alert_data.get("resort_name", "Test Resort")
        category = alert_data.get("alert_category", "moderate")
        snow_amount = alert_data.get("snow_amount", 8.5)
        forecast_amount = alert_data.get("forecast_amount", 0)
        temperature = alert_data.get("temperature", 32.0)
        conditions = alert_data.get("conditions", "Snow")

        # Create a synthetic snow_data dict
        snow_data = {
            "current_snow": snow_amount,
            "forecast_snow": forecast_amount,
            "current_temp": temperature,
            "conditions": conditions,
        }

        resort_metadata = {
            "region": alert_data.get("region", "Test Region"),
            "elevation": "9,000",
            "website": "https://example.com",
        }
    else:
        # Format the snowfall amount with one decimal place
        snow_amount = snow_data.get("current_snow", 0)

    # Choose emoji based on category
    emoji = "❄️"  # Default for light
    if category == "moderate":
        emoji = "🏂"
    elif category == "heavy":
        emoji = "🏔️"

    # Create message payload
    message = {
        "text": f"{emoji} {category.title()} Snow Alert: {resort_name}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {category.title()} Snow Alert: {resort_name}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{snow_amount:.1f} inches* of fresh snow at *{resort_name}*!",
                },
            },
        ],
    }

    # Add test indicator if needed
    if test:
        message["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🧪 *TEST NOTIFICATION* - This is a demo alert",
                },
            }
        )

    # Add resort metadata if available
    if resort_metadata:
        metadata_text = []

        if "elevation" in resort_metadata:
            metadata_text.append(f"Elevation: {resort_metadata['elevation']} ft")

        if "region" in resort_metadata:
            metadata_text.append(f"Region: {resort_metadata['region']}")

        if "website" in resort_metadata:
            metadata_text.append(f"<{resort_metadata['website']}|Resort Website>")

        if metadata_text:
            message["blocks"].append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": " | ".join(metadata_text)},
                }
            )

    # Add forecast information if available
    if snow_data.get("forecast_snow"):
        message["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Forecast*: Additional {snow_data['forecast_snow']:.1f} inches expected in the next 24 hours.",
                },
            }
        )

    # Add timestamp
    message["blocks"].append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Recorded at: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}",
                }
            ],
        }
    )

    # Skip sending if notifications are disabled
    if os.environ.get("DISABLE_NOTIFICATIONS", "").lower() == "true":
        logger.info(f"Notifications disabled, skipping alert for {resort_name}")
        return True

    # Send to Slack alerts channel
    try:
        logger.info(f'Sending snow alert for {resort_name} ({snow_amount:.1f}")')
        response = requests.post(SLACK_WEBHOOK_URL, json=message)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {str(e)}")
        return False


def send_status_update(
    results: Dict = None,
    errors: List[str] = None,
    alerts_sent: List[Dict] = None,
    status_data: Dict = None,
    test: bool = False,
) -> bool:
    """
    Send a status update to the monitoring Slack channel.

    Args:
        results: Processing results by resort
        errors: List of errors encountered
        alerts_sent: List of alerts that were sent
        status_data: Consolidated status data (used for testing)
        test: Whether this is a test notification

    Returns:
        Boolean indicating if the status was sent successfully
    """
    # Check if webhook URL is available
    if not SLACK_MONITORING_WEBHOOK_URL:
        logger.error("SLACK_MONITORING_WEBHOOK_URL environment variable not set")
        return False

    # Use status_data in test mode if provided
    if test and status_data:
        resorts_processed = status_data.get("resorts_processed", 0)
        alerts_triggered = status_data.get("alerts_triggered", 0)
        processing_time_ms = status_data.get("processing_time_ms", 0)
        error_count = status_data.get("errors", 0)
        error_list = (
            [f"Test error {i+1}" for i in range(error_count)]
            if isinstance(error_count, int)
            else []
        )
        alert_list = []
        results = {}  # Empty dict for test mode
    else:
        # Count the number of resorts processed and alerts triggered
        resorts_processed = len(results) if results else 0
        alerts_triggered = (
            sum(1 for r in results.values() if r.get("alert_triggered"))
            if results
            else 0
        )
        processing_time_ms = 0
        alert_list = alerts_sent or []
        error_list = errors or []

    # Determine overall status
    status = "✅ Operational" if not error_list else "⚠️ Issues detected"

    # For test mode, always set a specific status
    if test:
        status = "🧪 Test Status Update"

    # Create message payload
    message = {
        "text": f"Snowfall Alert System Status: {status}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Snowfall Alert System Status: {status}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{status}*\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S MT')}\n*Resorts Checked:* {resorts_processed}",
                },
            },
        ],
    }

    # Add processing time if available
    if processing_time_ms > 0:
        message["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Processing Time:* {processing_time_ms:.2f}ms",
                },
            }
        )

    # Add test indicator if needed
    if test:
        message["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🧪 *TEST NOTIFICATION* - This is a demo status update",
                },
            }
        )

    # Add alerts sent information
    if alert_list:
        alerts_text = "\n".join(
            [
                f"• {alert['resort']}: {alert['snow_amount']:.1f}\" - {alert['category']} alert"
                for alert in alert_list
            ]
        )
        message["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Alerts Sent ({len(alert_list)}):*\n{alerts_text}",
                },
            }
        )
    elif alerts_triggered > 0:
        message["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Alerts Triggered:* {alerts_triggered}",
                },
            }
        )

    # Add errors if any
    if error_list:
        errors_text = "\n".join([f"• {error}" for error in error_list[:5]])
        if len(error_list) > 5:
            errors_text += f"\n• ...and {len(error_list) - 5} more"

        message["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Errors ({len(error_list)}):*\n{errors_text}",
                },
            }
        )

    # Add resort details - sort by snow amount (descending)
    if results and not test:  # Skip in test mode
        # Extract resort names and snow amounts (if available)
        resort_snow = []
        for resort_name, result in results.items():
            if result.get("error") or result.get("skipped", False):
                continue

            if "primary_data" in result:
                snow = result["primary_data"].get("current_snow", 0)
                resort_snow.append((resort_name, snow))

        # Sort by snow amount (descending)
        resort_snow.sort(key=lambda x: x[1], reverse=True)

        # Format the text
        if resort_snow:
            resorts_text = "\n".join(
                [f'• {name}: {snow:.1f}"' for name, snow in resort_snow[:5]]
            )
            if len(resort_snow) > 5:
                resorts_text += f"\n• ...and {len(resort_snow) - 5} more"

            message["blocks"].append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Top Snow Depths:*\n{resorts_text}",
                    },
                }
            )

    # Send the message
    try:
        # Make the HTTP request to the Slack webhook
        with ExecutionTimer("send_status_slack", logger):
            response = requests.post(
                SLACK_MONITORING_WEBHOOK_URL, json=message, timeout=5
            )

        # Log the response
        if response.status_code == 200:
            logger.info("Status update sent to Slack successfully")
            return True
        else:
            logger.error(
                f"Failed to send status update to Slack: {response.status_code} - {response.text}"
            )
            return False

    except Exception as e:
        logger.exception(f"Error sending status update to Slack: {str(e)}")
        return False


# For local testing
if __name__ == "__main__":
    # Mock event and context
    test_event = {}
    test_context = None

    # Call the handler
    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))
