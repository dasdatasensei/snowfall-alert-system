"""
Tests for the logging configuration.

This module contains tests for the logging utilities to ensure they work as expected.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
import structlog

from src.utils.logging import get_logger, ExecutionTimer, log_lambda_context


def test_get_logger():
    """Test that get_logger returns a properly configured logger."""
    logger = get_logger("test_logger")

    # Check that we get a BoundLogger instance
    assert isinstance(logger, structlog.stdlib.BoundLogger)

    # Check that the logger has the expected bound values
    assert logger._context.get("application") == "snowfall_alert_system"
    assert "environment" in logger._context


def test_execution_timer_context_manager():
    """Test that ExecutionTimer works as a context manager."""
    mock_logger = MagicMock()

    with ExecutionTimer("test_operation", mock_logger):
        time.sleep(0.01)  # Small delay to ensure measurable time

    # Check that the logger was called for both start and end
    assert mock_logger.debug.call_count == 1
    assert mock_logger.info.call_count == 1

    # Verify the completion log has execution time
    completion_call = mock_logger.info.call_args[0][0]
    assert "Completed test_operation" in completion_call

    # Check that execution_time_seconds and execution_time_ms were logged
    kwargs = mock_logger.info.call_args[1]
    assert "execution_time_seconds" in kwargs
    assert "execution_time_ms" in kwargs

    # Verify the execution time is reasonable (greater than 0)
    assert kwargs["execution_time_seconds"] > 0
    assert kwargs["execution_time_ms"] > 0


def test_execution_timer_decorator():
    """Test that ExecutionTimer works as a decorator."""
    mock_logger = MagicMock()

    @ExecutionTimer("decorated_operation", mock_logger)
    def sample_function():
        time.sleep(0.01)  # Small delay
        return "result"

    result = sample_function()

    # Check the function still returns correctly
    assert result == "result"

    # Check logger calls
    assert mock_logger.debug.call_count == 1
    assert mock_logger.info.call_count == 1


def test_log_lambda_context():
    """Test that log_lambda_context correctly logs Lambda context information."""
    mock_logger = MagicMock()

    # Create a mock AWS Lambda context
    mock_context = MagicMock()
    mock_context.aws_request_id = "test-request-id"
    mock_context.function_name = "test-function"
    mock_context.function_version = "$LATEST"
    mock_context.memory_limit_in_mb = 128
    mock_context.log_group_name = "/aws/lambda/test-function"
    mock_context.log_stream_name = "2025/03/21/[$LATEST]abcdef123456"
    mock_context.get_remaining_time_in_millis = MagicMock(return_value=60000)

    # Call the function
    log_lambda_context(mock_logger, mock_context)

    # Verify the logger was called with expected information
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args[0]
    kwargs = mock_logger.info.call_args[1]

    assert "Lambda context" in call_args
    assert kwargs["aws_request_id"] == "test-request-id"
    assert kwargs["function_name"] == "test-function"
    assert kwargs["function_version"] == "$LATEST"
    assert kwargs["memory_limit_in_mb"] == 128
    assert kwargs["log_group_name"] == "/aws/lambda/test-function"
    assert kwargs["log_stream_name"] == "2025/03/21/[$LATEST]abcdef123456"
    assert kwargs["remaining_time_ms"] == 60000


def test_log_lambda_context_handles_exception():
    """Test that log_lambda_context handles exceptions gracefully."""
    mock_logger = MagicMock()

    # Create a mock context that raises an exception when accessed
    class ExceptionRaisingContext:
        @property
        def aws_request_id(self):
            raise Exception("Test exception")

    mock_context = ExceptionRaisingContext()

    # Call the function
    log_lambda_context(mock_logger, mock_context)

    # Verify the function logs a warning instead of failing
    mock_logger.warning.assert_called_once()

    # Check that the warning message contains expected content
    warning_args = mock_logger.warning.call_args[0][0]
    assert "Failed to log Lambda context" in warning_args
    assert "Test exception" in warning_args
