# Setup Guide

This guide provides step-by-step instructions for setting up the Snowfall Alert System on AWS Lambda with Slack integration.

## Prerequisites

Before you begin, ensure you have:

- AWS account with permission to create Lambda functions
- Slack workspace where you can create apps and webhooks
- OpenWeatherMap API key ([Get one here](https://openweathermap.org/api))
- WeatherAPI.com API key ([Get one here](https://www.weatherapi.com/))
- Python 3.9+ installed locally
- Git installed
- pip and virtualenv installed

## 1. Local Development Environment Setup

### Clone the Repository

```bash
git clone https://github.com/yourusername/snowfall-alert-system.git
cd snowfall-alert-system
```

### Set Up Python Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r src/requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root:

```
# API Keys
OPENWEATHER_API_KEY=your_openweathermap_api_key
WEATHERAPI_KEY=your_weatherapi_key

# Slack Configuration
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLACK_MONITORING_WEBHOOK_URL=your_monitoring_webhook_url

# Application Settings
LOG_LEVEL=INFO
THRESHOLD_LIGHT=2
THRESHOLD_MODERATE=6
THRESHOLD_HEAVY=12
```

## 2. Slack Setup

### Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" > "From scratch"
3. Name your app (e.g., "Snowfall Alerts") and select your workspace
4. Click "Create App"

### Configure Incoming Webhooks

1. In the left sidebar, click "Incoming Webhooks"
2. Toggle "Activate Incoming Webhooks" to On
3. Click "Add New Webhook to Workspace"
4. Select the channel where alerts should be posted (create a new channel if needed)
5. Click "Allow"
6. Copy the Webhook URL provided

### Create a Monitoring Channel (Optional)

1. Create a new channel in Slack (e.g., #snowalert-monitoring)
2. Repeat the webhook setup process for this channel
3. Update your .env file with both webhook URLs

## 3. AWS Lambda Deployment

### Prepare Deployment Package

```bash
# Create a deployment directory
mkdir -p deployment/package

# Copy source code
cp -R src/* deployment/package/

# Install dependencies in the package directory
pip install -r src/requirements.txt -t deployment/package/

# Zip the package
cd deployment/package
zip -r ../deployment.zip .
cd ../..
```

### Create Lambda Function

1. Open the AWS Management Console
2. Navigate to Lambda service
3. Click "Create function"
4. Select "Author from scratch"
5. Configure basic information:
   - Name: `SnowfallAlertSystem`
   - Runtime: Python 3.9
   - Architecture: x86_64
   - Permissions: Create a new role with basic Lambda permissions
6. Click "Create function"

### Upload Deployment Package

1. In the Lambda function page, under "Code source", click "Upload from" > ".zip file"
2. Upload the `deployment/deployment.zip` file
3. Click "Save"

### Configure Lambda Settings

1. Set the Handler to: `lambda_function.lambda_handler`
2. Configure environment variables:
   - `OPENWEATHER_API_KEY`: Your OpenWeatherMap API key
   - `WEATHERAPI_KEY`: Your Weather API key
   - `SLACK_WEBHOOK_URL`: Your Slack webhook URL for alerts
   - `SLACK_MONITORING_WEBHOOK_URL`: Your monitoring webhook URL (optional)
   - `LOG_LEVEL`: INFO
   - `THRESHOLD_LIGHT`: 2
   - `THRESHOLD_MODERATE`: 6
   - `THRESHOLD_HEAVY`: 12
3. Under "General configuration":
   - Memory: 128 MB
   - Timeout: 30 seconds
   - Configure these settings by clicking "Edit"

## 4. Set Up Scheduled Execution

### Create CloudWatch Events Rule

1. Navigate to CloudWatch service
2. In the left sidebar, click "Events" > "Rules"
3. Click "Create rule"
4. For "Event Source", select "Schedule"
5. Choose "Fixed rate" and set interval (e.g., 6 hours)
6. Click "Add target"
7. Select "Lambda function" and choose your `SnowfallAlertSystem` function
8. Click "Configure details"
9. Name the rule (e.g., `SnowfallAlertSchedule`)
10. Click "Create rule"

## 5. Testing the Deployment

### Test the Lambda Function

1. In the Lambda console, click the "Test" tab
2. Create a new test event with an empty JSON object `{}`
3. Click "Test" to execute the function
4. Check the Execution results
5. Verify that a message appears in your Slack channel

### Verify CloudWatch Logs

1. Navigate to CloudWatch > Logs > Log groups
2. Find the log group for your Lambda function (/aws/lambda/SnowfallAlertSystem)
3. Check the latest log stream for execution details and any errors

## 6. Customizing Resort Configuration

To modify the list of monitored resorts:

1. Open `src/config/resorts.py`
2. Add or remove resorts and their coordinates as needed:
   ```python
   RESORTS = {
       "Resort Name": (latitude, longitude),
       # Additional resorts...
   }
   ```
3. Redeploy the Lambda function after changes

## 7. Adjusting Snow Thresholds

To customize the snowfall thresholds:

1. Update the environment variables in the Lambda console:

   - `THRESHOLD_LIGHT`: Minimum inches for light snow alert
   - `THRESHOLD_MODERATE`: Minimum inches for moderate snow alert
   - `THRESHOLD_HEAVY`: Minimum inches for heavy snow alert

2. Alternatively, modify `src/config/thresholds.py` and redeploy:
   ```python
   THRESHOLDS = {
       "light": 2,      # 2+ inches in 24 hours
       "moderate": 6,   # 6+ inches in 24 hours
       "heavy": 12      # 12+ inches in 24 hours
   }
   ```

## Troubleshooting

### Common Issues and Solutions

#### Lambda Function Errors

- **Issue**: Function execution fails with timeout

  - **Solution**: Increase the Lambda timeout in configuration

- **Issue**: API rate limit exceeded
  - **Solution**: Reduce check frequency or upgrade API plan

#### Slack Integration Problems

- **Issue**: No messages appearing in Slack

  - **Solution**: Verify webhook URL is correct and channel exists

- **Issue**: Missing permissions for webhook
  - **Solution**: Reinstall the Slack app to workspace with correct permissions

#### AWS CloudWatch Schedule Issues

- **Issue**: Function not triggering automatically
  - **Solution**: Check CloudWatch Events rule is enabled and correctly configured

## Next Steps

After completing the setup:

1. Monitor the system for a few days to ensure reliable operation
2. Adjust snowfall thresholds based on your preferences
3. Consider implementing the enhancements listed in the Future Enhancements section
