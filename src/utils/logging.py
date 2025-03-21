"""
Logging configuration for the Snowfall Alert System.

This module provides a centralized logging configuration that can be used
throughout the application. It sets up structured logging using structlog
along with Python's built-in logging module.
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get log level from environment or default to INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL_NUM = getattr(logging, LOG_LEVEL, logging.INFO)

# Configure structlog processors
structlog_processors = [
    # Add timestamps in ISO format
    structlog.processors.TimeStamper(fmt="iso"),
    # Add log level name
    structlog.processors.add_log_level,
    # Include the logger name - fixing the error with compatible approach
    structlog.stdlib.add_logger_name,
    # Format exceptions
    structlog.processors.ExceptionPrettyPrinter(),
    # Format the final output as JSON for cloud environments
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

# Add different renderers based on environment
if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):  # When running in AWS Lambda
    structlog_processors.append(structlog.processors.JSONRenderer())
else:  # When running locally
    structlog_processors.append(
        structlog.dev.ConsoleRenderer(colors=True, sort_keys=True)
    )

# Configure structlog
structlog.configure(
    processors=structlog_processors,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Setup basic configuration for the Python standard logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=LOG_LEVEL_NUM,
)


# Create a new logger with our custom configuration
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger with the given name.

    Args:
        name: The name of the logger, typically __name__ from the calling module.

    Returns:
        A structured logger configured according to the application settings.
    """
    logger = structlog.get_logger(name)
    # Add runtime context that's useful for all logs
    logger = logger.bind(
        application="snowfall_alert_system",
        environment=os.getenv("ENVIRONMENT", "development"),
    )
    return logger


# Create a helper function for AWS Lambda context logging
def log_lambda_context(logger: structlog.stdlib.BoundLogger, context: Any) -> None:
    """
    Log useful information from the AWS Lambda context.

    Args:
        logger: The structured logger to use.
        context: The AWS Lambda context object.
    """
    if not context:
        return

    try:
        logger.info(
            "Lambda context",
            aws_request_id=getattr(context, "aws_request_id", "unknown"),
            function_name=getattr(context, "function_name", "unknown"),
            function_version=getattr(context, "function_version", "unknown"),
            memory_limit_in_mb=getattr(context, "memory_limit_in_mb", "unknown"),
            log_group_name=getattr(context, "log_group_name", "unknown"),
            log_stream_name=getattr(context, "log_stream_name", "unknown"),
            remaining_time_ms=getattr(
                context, "get_remaining_time_in_millis", lambda: "unknown"
            )(),
        )
    except Exception as e:
        # Ensure we use a string format that will work with structlog
        logger.warning(f"Failed to log Lambda context: {str(e)}")


# Timer for measuring execution time
class ExecutionTimer:
    """
    Timer utility for measuring and logging execution time of code blocks.
    Can be used as a context manager or decorator.
    """

    def __init__(
        self, name: str, logger: Optional[structlog.stdlib.BoundLogger] = None
    ):
        """
        Initialize the timer.

        Args:
            name: A name for this timer (for logging).
            logger: The logger to use. If None, a new logger will be created.
        """
        self.name = name
        self.logger = logger or get_logger("timer")
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        """Start the timer when entering a context."""
        self.start_time = time.time()
        self.logger.debug(f"Started {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer when exiting a context and log the execution time."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        self.logger.info(
            f"Completed {self.name}",
            execution_time_seconds=round(duration, 3),
            execution_time_ms=round(duration * 1000, 1),
        )

    def __call__(self, func):
        """Allow this timer to be used as a decorator."""

        def wrapped(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapped


# Example usage
if __name__ == "__main__":
    # Get a logger for this module
    logger = get_logger(__name__)

    # Log some test messages
    logger.debug("This is a debug message")
    logger.info("This is an info message", extra_field="some value")
    logger.warning("This is a warning message", code=123)

    # Example of using the timer as a context manager
    with ExecutionTimer("example task", logger):
        logger.info("Doing some work...")
        time.sleep(0.5)  # Simulate work

    # Example of catching and logging an exception
    try:
        raise ValueError("This is a test exception")
    except Exception:
        logger.exception("An error occurred")
