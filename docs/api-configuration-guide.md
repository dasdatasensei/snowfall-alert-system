# API Configuration Guide

This document provides step-by-step instructions for obtaining and configuring the necessary API keys for the Snowfall Alert System.

## Overview

The Snowfall Alert System requires two weather API services:

1. OpenWeatherMap - primary data source
2. WeatherAPI.com - secondary source for verification

This guide will walk you through setting up accounts, obtaining API keys, and properly configuring them for use in the application.

## OpenWeatherMap Setup

### Create an Account

1. Visit [OpenWeatherMap Sign Up](https://home.openweathermap.org/users/sign_up)
2. Fill in the registration form with your details
3. Verify your email address

### Get API Key

1. Log in to your account
2. Navigate to the "API keys" tab
3. You'll see a default API key has been generated for you
4. Optionally, create a new named key specifically for this project

![OpenWeatherMap API Keys](../assets/openweathermap-keys.png)

### Activate One Call API

1. Go to the [OpenWeatherMap API](https://openweathermap.org/api) page
2. Select "One Call API"
3. Subscribe to the free tier:
   - 1,000 API calls/day
   - Current weather and forecast
   - 5 days of historical data
4. Note: API keys may take up to 2 hours to activate after initial creation

### Test Your API Key

Test that your API key is working with the following curl command (replace YOUR_API_KEY):

```bash
curl "https://api.openweathermap.org/data/2.5/onecall?lat=40.6514&lon=-111.5080&exclude=minutely,hourly&units=imperial&appid=YOUR_API_KEY"
```

You should receive a JSON response with weather data for Park City.

## WeatherAPI.com Setup

### Create an Account

1. Visit [WeatherAPI.com Sign Up](https://www.weatherapi.com/signup.aspx)
2. Create a free account
3. Verify your email address

### Get API Key

1. After verification, you'll be taken to your dashboard
2. Your API key will be displayed prominently
3. Copy this key for use in the application

![WeatherAPI.com Dashboard](../assets/weatherapi-dashboard.png)

### Free Tier Limits

The free tier includes:

- 1,000,000 calls per month
- 1 call per second rate limit
- Forecast data for up to 3 days
- Historical weather for the last 7 days
- No credit card required

### Test Your API Key

Verify your API key is working with this curl command (replace YOUR_API_KEY):

```bash
curl "https://api.weatherapi.com/v1/forecast.json?key=YOUR_API_KEY&q=40.6514,-111.5080&days=1"
```

You should receive a JSON response with weather data for the Park City area.

## Configuring API Keys in the Application

### Local Development

For local development, add the API keys to your `.env` file:

```
OPENWEATHER_API_KEY=your_openweathermap_api_key
WEATHERAPI_KEY=your_weatherapi_key
```

### AWS Lambda Configuration

1. Go to the AWS Lambda console
2. Select your Snowfall Alert System function
3. Navigate to the "Configuration" tab
4. Select "Environment variables"
5. Add the following variables:
   - Key: `OPENWEATHER_API_KEY`, Value: your OpenWeatherMap API key
   - Key: `WEATHERAPI_KEY`, Value: your WeatherAPI.com API key
6. Click "Save"

![Lambda Environment Variables](../assets/lambda-env-vars.png)

## API Usage Monitoring

### Monitor OpenWeatherMap Usage

1. Log in to your OpenWeatherMap account
2. Go to the "API keys" tab
3. You'll see usage statistics for each key

### Monitor WeatherAPI.com Usage

1. Log in to your WeatherAPI.com dashboard
2. Navigate to the "Usage" tab
3. View your current usage and limits

### Setting Up Usage Alerts

To avoid exceeding free tier limits:

1. Add code to log API usage counts to CloudWatch Metrics
2. Set up CloudWatch Alarms when approaching limits (e.g., 80% of daily limit)
3. Add logic to your Lambda function to degrade gracefully if limits are reached

## API Key Security Best Practices

1. **Never commit API keys to your repository**

   - Use environment variables or AWS Parameter Store
   - Add `.env` files to `.gitignore`

2. **Restrict API key usage**

   - Set up IP restrictions if supported by the API provider
   - Use the principle of least privilege

3. **Regular rotation**

   - Consider rotating API keys quarterly for better security
   - Update environment variables after rotation

4. **Monitor for unauthorized use**
   - Regularly check API usage statistics
   - Watch for unexpected spikes in usage

## Troubleshooting

### OpenWeatherMap Issues

- **"Invalid API key" error**: Ensure the key is entered correctly and has been activated
- **"Unauthorized" error**: API key may take up to 2 hours to activate after creation
- **Rate limiting**: Check if you've exceeded the 1,000 calls/day limit

### WeatherAPI.com Issues

- **Authentication error**: Verify the API key is correct
- **Too many requests**: Respect the 1 call/second rate limit by adding delays
- **Invalid location**: Check that coordinates are properly formatted

## Additional Resources

- [OpenWeatherMap API Documentation](https://openweathermap.org/api/one-call-api)
- [WeatherAPI.com Documentation](https://www.weatherapi.com/docs/)
- [AWS Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
