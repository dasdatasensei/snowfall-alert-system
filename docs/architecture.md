# System Architecture

This document outlines the architecture of the Snowfall Alert System, detailing its components, data flow, and design decisions.

## Architecture Overview

The Snowfall Alert System follows a serverless architecture pattern, leveraging cloud services to create a lightweight, scalable solution. The system runs entirely on AWS Lambda with Slack integration for notifications, eliminating the need for managing servers.

![Architecture Diagram](../assets/snowfall_alert_sys_arch.png)

## Core Components

### 1. AWS Lambda Function

**Purpose**: Central processing component that retrieves weather data, analyzes snowfall conditions, and sends notifications.

**Key Characteristics**:

- Runtime: Python 3.9
- Memory Allocation: 128 MB
- Execution Timeout: 30 seconds
- Trigger: CloudWatch Events schedule (every 6 hours)

**Responsibilities**:

- Retrieve data from weather APIs
- Compare data against thresholds
- Verify data accuracy using multiple sources
- Send alerts when conditions are met
- Log execution details and errors
- Send monitoring updates

### 2. CloudWatch Events

**Purpose**: Scheduled trigger for Lambda execution.

**Configuration**:

- Schedule expression: rate(6 hours)
- Target: Snowfall Alert Lambda function
- Input: Empty event {}

### 3. External APIs

#### OpenWeatherMap API

**Purpose**: Primary source of snowfall data.

**Integration Points**:

- One Call API endpoint for current and forecast data
- Snow accumulation data in imperial units (inches)

#### WeatherAPI.com

**Purpose**: Secondary source for data verification.

**Integration Points**:

- Forecast API endpoint
- Snow accumulation data in metric units (cm)

### 4. Slack Integration

**Purpose**: Notification delivery and monitoring dashboard.

**Components**:

- Webhook-based integration (no persistent connection)
- Main alerts channel for snowfall notifications
- Monitoring channel for system status updates

## Data Flow

1. **Scheduled Trigger**: CloudWatch Events initiates Lambda function execution every 6 hours.

2. **Weather Data Retrieval**:

   - Lambda function retrieves snowfall data for each configured resort from OpenWeatherMap API.
   - If significant snowfall is detected, the function verifies with WeatherAPI.com.

3. **Data Processing**:

   - Snowfall amounts are compared against configured thresholds.
   - Data from multiple sources is compared for accuracy.

4. **Alert Generation**:

   - If verified snowfall exceeds thresholds, an alert notification is formatted.
   - Alert includes resort name, snowfall amount, and timestamp.

5. **Notification Delivery**:

   - Alerts are sent to the main Slack channel via webhook.
   - Status updates are sent to the monitoring channel.

6. **Logging and Monitoring**:
   - Execution details and any errors are logged to CloudWatch Logs.
   - Status messages in Slack provide system health information.

## Code Structure

The project follows a modular structure with clear separation of concerns:

```
snowfall-alert-system/
├── src/
│   ├── weather/          # Weather API integration
│   │   ├── apis.py       # API client implementation
│   │   ├── models.py     # Data models
│   │   └── utils.py      # Helper functions
│   ├── notifications/    # Slack notification handling
│   │   ├── slack.py      # Webhook implementation
│   │   └── formatters.py # Message formatting
│   ├── config/           # Configuration
│   │   ├── resorts.py    # Resort coordinates
│   │   └── thresholds.py # Snowfall thresholds
│   ├── utils/            # Utilities
│   │   └── logging.py    # Logging configuration
│   └── lambda_function.py # Main entry point
```

## Design Decisions

### 1. Serverless Architecture

**Decision**: Use AWS Lambda instead of EC2 or other server-based solutions.

**Rationale**:

- No server maintenance required
- Pay only for execution time
- Automatic scaling and high availability
- Sufficient for periodic checks with minimal resource requirements

### 2. Multi-Source Data Verification

**Decision**: Use two separate weather data sources and verify snowfall reports.

**Rationale**:

- Weather forecasting is inherently imprecise
- Mountain weather can vary significantly from general forecasts
- Reduces false positives by requiring multiple sources to agree
- Increases confidence in alerts

### 3. Slack for Notifications and Monitoring

**Decision**: Use Slack for both alerts and system monitoring instead of separate monitoring tools.

**Rationale**:

- Simplifies architecture (single notification channel)
- Provides built-in history and search functionality
- Mobile and desktop accessibility
- Eliminates need for a separate web dashboard
- Simple message formatting for status visualization

### 4. Scheduled Execution vs. Event-Driven

**Decision**: Use scheduled execution rather than event-driven architecture.

**Rationale**:

- Weather data doesn't provide native events/webhooks
- Regular checks are sufficient for snowfall monitoring
- Simplifies implementation and reduces complexity
- 6-hour interval balances timeliness with API usage

## Scalability Considerations

While designed for monitoring 10 ski resorts, the system can scale to handle more:

- **Resort Scaling**: The design can handle dozens of resorts without modification.
- **Frequency Scaling**: Check frequency can be increased up to hourly while staying within free API limits.
- **Regional Scaling**: Additional regions can be monitored by deploying separate instances of the system.

## Security Considerations

1. **API Key Management**:

   - Keys stored as environment variables, not in code
   - Lambda execution role with minimal permissions

2. **Slack Integration**:

   - Incoming webhook only (no read access to channels)
   - Separate webhooks for alerts and monitoring

3. **Error Handling**:
   - Sensitive information scrubbed from error messages
   - Failed API calls don't expose authentication details

## Future Architecture Enhancements

1. **Data Persistence**:

   - Add DynamoDB for historical snowfall data storage
   - Enable trend analysis and visualization

2. **Enhanced Monitoring**:

   - CloudWatch Alarms for Lambda errors
   - SNS notifications for system failures

3. **Web Dashboard**:
   - Simple static website for historical data visualization
   - Resort comparison features
   - Hosted on S3 with CloudFront
