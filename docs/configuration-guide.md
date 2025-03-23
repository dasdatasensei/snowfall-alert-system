# Configuration Guide

This document explains how to configure the Snowfall Alert System using environment variables and configuration files.

## Environment Variables

The system uses environment variables for configuration. These can be set in your AWS Lambda environment or in a local `.env` file for development.

### Required Variables

| Variable              | Description                 | Example                                                |
| --------------------- | --------------------------- | ------------------------------------------------------ |
| `OPENWEATHER_API_KEY` | API key for OpenWeatherMap  | `abcdef123456789`                                      |
| `WEATHERAPI_KEY`      | API key for WeatherAPI.com  | `abcdef123456789`                                      |
| `SLACK_WEBHOOK_URL`   | Webhook URL for snow alerts | `https://hooks.slack.com/services/TXXXXX/BXXXXX/XXXXX` |

### Optional Variables

| Variable                       | Description                                            | Default                     | Example                                                |
| ------------------------------ | ------------------------------------------------------ | --------------------------- | ------------------------------------------------------ |
| `SLACK_MONITORING_WEBHOOK_URL` | Webhook URL for monitoring channel                     | Same as `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/services/TXXXXX/BXXXXX/XXXXX` |
| `LOG_LEVEL`                    | Logging level                                          | `INFO`                      | `DEBUG`                                                |
| `VERIFICATION_THRESHOLD`       | Maximum allowable difference (inches) between sources  | `2.0`                       | `3.5`                                                  |
| `ALERT_COOLDOWN_HOURS`         | Hours before sending another alert for the same resort | `12`                        | `24`                                                   |
| `THRESHOLD_LIGHT`              | Minimum inches for light snow alert                    | `2`                         | `3`                                                    |
| `THRESHOLD_MODERATE`           | Minimum inches for moderate snow alert                 | `6`                         | `7`                                                    |
| `THRESHOLD_HEAVY`              | Minimum inches for heavy snow alert                    | `12`                        | `10`                                                   |
| `CHECK_FREQUENCY`              | Hours between checks (for testing)                     | `6`                         | `3`                                                    |

## Configuration Files

The system's configuration is split across several files:

### `src/config/settings.py`

Central configuration file that loads environment variables and provides access to all settings.

### `src/config/resorts.py`

Defines the ski resorts to be monitored, with their coordinates:

```python
RESORTS = {
    "Park City Mountain": (40.6514, -111.5080),
    "Deer Valley": (40.6374, -111.4783),
    # ... other resorts
}
```

To modify this list, edit the file directly or override it in your Lambda function.

### `src/config/thresholds.py`

Defines snowfall thresholds for different alert levels:

```python
THRESHOLDS = {
    "light": float(os.environ.get("THRESHOLD_LIGHT", "2")),
    "moderate": float(os.environ.get("THRESHOLD_MODERATE", "6")),
    "heavy": float(os.environ.get("THRESHOLD_HEAVY", "12"))
}
```

## Configuration Best Practices

1. **Never commit API keys or webhooks to version control**

   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Use AWS Lambda environment variables for production**

   - Set these in the Lambda Console or using Infrastructure as Code
   - Encrypted at rest by AWS

3. **Use local `.env` file for development**

   - Create a `.env` file in the project root
   - Format: `VARIABLE_NAME=value`

4. **Validate configuration at startup**

   - The system checks for required variables when started
   - Missing variables are logged as errors

5. **Consider AWS Parameter Store for sensitive values**
   - Alternative to environment variables
   - Provides versioning and better security

## Local Development Configuration

For local development, create a `.env` file in the project root with your configuration:

```bash
# API Keys
OPENWEATHER_API_KEY=your_openweather_api_key_here
WEATHERAPI_KEY=your_weatherapi_key_here
VISUALCROSSING_API_KEY=your_visualcrossing_api_key_here

# Slack Webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/TXXXXX/BXXXXX/XXXXX
SLACK_MONITORING_WEBHOOK_URL=https://hooks.slack.com/services/TXXXXX/BXXXXX/XXXXX

# Application Settings
LOG_LEVEL=DEBUG
VERIFICATION_THRESHOLD=2.0
ALERT_COOLDOWN_HOURS=12

# Snowfall Thresholds
THRESHOLD_LIGHT=2
THRESHOLD_MODERATE=6
THRESHOLD_HEAVY=12
```

## AWS Lambda Configuration

In the AWS Lambda console:

1. Navigate to your function
2. Select the "Configuration" tab
3. Click on "Environment variables"
4. Add each variable as a key-value pair
5. Click "Save"

![Lambda Environment Variables](../assets/lambda-env-vars.png)

## Modifying Resort List

To add or remove resorts from monitoring:

1. Edit `src/config/resorts.py`
2. Add new resorts with coordinates:
   ```python
   "New Resort Name": (latitude, longitude)
   ```
3. Remove resorts by deleting their entry
4. Redeploy the Lambda function

## Adjusting Snowfall Thresholds

Snowfall thresholds can be adjusted in two ways:

1. **Environment Variables (recommended)**:

   - Set `THRESHOLD_LIGHT`, `THRESHOLD_MODERATE`, and `THRESHOLD_HEAVY`
   - No code changes required

2. **Code Changes**:
   - Modify `src/config/thresholds.py`
   - Redeploy the Lambda function

## Troubleshooting Configuration Issues

If you encounter configuration-related errors:

1. **Check Environment Variables**:

   - Verify all required variables are set
   - Check for typos in variable names

2. **Verify API Keys**:

   - Test API keys directly using curl or Postman
   - Regenerate keys if necessary

3. **Validate Webhook URLs**:

   - Test webhooks with a simple curl command:
     ```bash
     curl -X POST -H "Content-type: application/json" \
     --data '{"text":"Test message"}' YOUR_WEBHOOK_URL
     ```

4. **Check Lambda Logs**:
   - Configuration validation errors are logged at startup
   - Look for messages about missing variables
