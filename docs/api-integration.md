# API Integration Documentation

This document details the external API integrations used in the Snowfall Alert System, including authentication methods, endpoints, request parameters, and response formats.

## Weather Data APIs

### OpenWeatherMap API

**Purpose:** Primary source of snowfall data for ski resorts.

**Base URL:** `https://api.openweathermap.org/data/2.5/`

**API Key:** Obtained from [OpenWeatherMap API Keys](https://home.openweathermap.org/api_keys) page after registration.

#### One Call API Endpoint

**URL:** `https://api.openweathermap.org/data/2.5/onecall`

**Method:** GET

**Parameters:**

- `lat` (required): Latitude of the resort location
- `lon` (required): Longitude of the resort location
- `exclude` (optional): Parts to exclude from response (e.g., "minutely,hourly")
- `units` (required): Units format - set to "imperial" for inches/Fahrenheit
- `appid` (required): Your API key

**Example Request:**

```
https://api.openweathermap.org/data/2.5/onecall?lat=40.6514&lon=-111.5080&exclude=minutely,hourly&units=imperial&appid=YOUR_API_KEY
```

**Authentication:**

- API key passed as query parameter (`appid`)
- HTTPS supported for secure transmission

**Response Format:**

```json
{
  "lat": 40.6514,
  "lon": -111.508,
  "timezone": "America/Denver",
  "timezone_offset": -21600,
  "current": {
    "dt": 1616953200,
    "temp": 28.4,
    "weather": [
      {
        "id": 601,
        "main": "Snow",
        "description": "snow",
        "icon": "13d"
      }
    ],
    "snow": {
      "1h": 2.5
    }
  },
  "daily": [
    {
      "dt": 1616954400,
      "temp": {
        "day": 32.5,
        "min": 24.8,
        "max": 35.6
      },
      "weather": [
        {
          "id": 601,
          "main": "Snow",
          "description": "snow",
          "icon": "13d"
        }
      ],
      "snow": 8.5
    }
  ]
}
```

**Key Fields:**

- `current.snow["1h"]`: Snowfall amount in last hour (inches)
- `daily[0].snow`: Snowfall amount for the day (inches)

**Rate Limits:**

- Free tier: 1,000 API calls/day
- Paid tiers available starting at $40/month for 100,000 calls/month

**Error Handling:**

- HTTP status codes indicate success/failure
- Error responses include a message field with details
- Implement exponential backoff for rate limit errors

### WeatherAPI.com

**Purpose:** Secondary source for data verification.

**Base URL:** `https://api.weatherapi.com/v1/`

**API Key:** Obtained from [WeatherAPI.com Dashboard](https://www.weatherapi.com/my/) after registration.

#### Forecast API Endpoint

**URL:** `https://api.weatherapi.com/v1/forecast.json`

**Method:** GET

**Parameters:**

- `q` (required): Query - either "latitude,longitude" or location name
- `days` (required): Number of forecast days (1-10)
- `key` (required): Your API key

**Example Request:**

```
https://api.weatherapi.com/v1/forecast.json?q=40.6514,-111.5080&days=2&key=YOUR_API_KEY
```

**Authentication:**

- API key passed as query parameter (`key`)
- HTTPS by default

**Response Format:**

```json
{
  "location": {
    "name": "Park City",
    "region": "Utah",
    "country": "United States of America",
    "lat": 40.65,
    "lon": -111.51,
    "tz_id": "America/Denver"
  },
  "current": {
    "temp_f": 28.4,
    "condition": {
      "text": "Light snow",
      "icon": "//cdn.weatherapi.com/weather/64x64/day/326.png"
    }
  },
  "forecast": {
    "forecastday": [
      {
        "date": "2023-03-21",
        "day": {
          "maxtemp_f": 35.6,
          "mintemp_f": 24.8,
          "totalsnow_cm": 21.6,
          "condition": {
            "text": "Heavy snow",
            "icon": "//cdn.weatherapi.com/weather/64x64/day/338.png"
          }
        },
        "hour": [
          {
            "time": "2023-03-21 00:00",
            "temp_f": 26.8,
            "condition": {
              "text": "Light snow",
              "icon": "//cdn.weatherapi.com/weather/64x64/night/326.png"
            },
            "chance_of_snow": 80,
            "snow_cm": 2.5
          }
        ]
      }
    ]
  }
}
```

**Key Fields:**

- `forecast.forecastday[0].day.totalsnow_cm`: Total snow for the day (cm, convert to inches)
- `forecast.forecastday[0].hour[x].snow_cm`: Snow per hour (cm, convert to inches)

**Rate Limits:**

- Free tier: 1,000,000 calls/month, max 1 call/second
- Paid tiers available starting at $10/month for 2 million calls/month

**Error Handling:**

- HTTP status codes indicate success/failure
- Error responses include an error object with details
- Add delay between requests to respect the 1 call/second limit

## Weather API Client Implementation

Our system implements a modular API client for interacting with both weather services. The implementation includes:

### Base Client Class Features

- Standardized request handling
- Response caching to reduce API calls
- Exponential backoff retry mechanism
- Comprehensive error handling and logging

### OpenWeatherMap Client

```python
# Example usage
from src.weather.client import OpenWeatherMapClient

# Create client instance
client = OpenWeatherMapClient()

# Get snowfall data for a resort
lat, lon = 40.6514, -111.5080  # Park City coordinates
snow_data = client.get_snow_data(lat, lon)

print(f"Current snow: {snow_data['current_snow']} inches")
print(f"Forecast snow: {snow_data['forecast_snow']} inches")
```

### WeatherAPI.com Client

```python
# Example usage
from src.weather.client import WeatherApiClient

# Create client instance
client = WeatherApiClient()

# Get snowfall data for a resort
lat, lon = 40.6514, -111.5080  # Park City coordinates
snow_data = client.get_snow_data(lat, lon)

print(f"Snow: {snow_data['snow_inches']} inches ({snow_data['snow_cm']} cm)")
```

### Verification Process

```python
# Example usage
from src.weather.client import verify_with_secondary_source

# Check if secondary source confirms snowfall amount
is_verified, secondary_data = verify_with_secondary_source(
    "Park City Mountain", 40.6514, -111.5080, 5.0
)

if is_verified:
    print("Snowfall verified by secondary source")
else:
    print("Snowfall verification failed")
```

## Slack API Integration

### Incoming Webhooks

**Purpose:** Send notifications to Slack channels.

**Webhook URL Format:** `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`

**Method:** POST

**Headers:**

- `Content-Type: application/json`

**Request Body Format:**

```json
{
  "text": "Optional plain text fallback",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🏔️ Heavy Snow Alert: Park City Mountain"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*8.5 inches* of fresh snow at *Park City Mountain*!"
      }
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "Recorded at: 2023-03-21 06:00 MT"
        }
      ]
    }
  ]
}
```

**Authentication:**

- Webhook URL contains authentication credentials
- HTTPS required for secure transmission
- No additional headers or parameters needed

**Response:**

- Success: HTTP 200 with body "ok"
- Error: HTTP error status with error message

**Rate Limits:**

- Tier 1 workspace: 1 message per second
- Implement queuing if sending multiple messages in quick succession

### Implementation Example

```python
import requests
import json
import os

def send_snow_alert(resort_name, snow_amount, category):
    """Send a snow alert to Slack."""

    # Slack webhook URL from environment variable
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    # Create message payload
    message = {
        "text": f"{category.title()} Snow Alert: {resort_name}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🏔️ {category.title()} Snow Alert: {resort_name}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{snow_amount:.1f} inches* of fresh snow at *{resort_name}*!"
                }
            }
        ]
    }

    # Send to Slack
    response = requests.post(webhook_url, json=message)

    # Check for success
    if response.status_code == 200 and response.text == "ok":
        return True
    else:
        raise Exception(f"Failed to send Slack message: {response.text}")
```

## Error Handling and Retries

The system implements robust error handling for all API requests:

### Exponential Backoff

For transient errors, the system uses exponential backoff to retry requests:

```python
def make_request_with_retries(url, params, max_retries=3, initial_delay=1.0):
    """Make an API request with exponential backoff retries."""

    retries = 0
    last_exception = None

    while retries < max_retries:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            last_exception = e
            retries += 1

            if retries < max_retries:
                sleep_time = initial_delay * (2 ** (retries - 1))  # Exponential backoff
                logging.warning(
                    f"Request failed, retrying in {sleep_time:.1f}s ({retries}/{max_retries}): {str(e)}"
                )
                time.sleep(sleep_time)
            else:
                logging.error(f"Request failed after {max_retries} attempts: {str(e)}")

    # If all retries failed, raise the last exception
    raise last_exception or Exception(f"Request to {url} failed for unknown reason")
```

### Response Caching

To reduce API calls and improve performance, the system implements a simple in-memory cache:

```python
def get_cached_or_fetch(cache, cache_key, fetch_func, ttl_seconds=300):
    """Get data from cache or fetch from API if not cached or expired."""

    now = datetime.now()

    # Check if cached and not expired
    if cache_key in cache and cache[cache_key]["expires"] > now:
        return cache[cache_key]["data"]

    # Fetch fresh data
    data = fetch_func()

    # Cache the result
    cache[cache_key] = {
        "data": data,
        "expires": now + timedelta(seconds=ttl_seconds)
    }

    return data
```

## Data Transformation Utilities

The system includes utilities for unit conversion:

```python
def cm_to_inches(cm):
    """Convert centimeters to inches."""
    return cm / 2.54

def mm_to_inches(mm):
    """Convert millimeters to inches."""
    return mm / 25.4

def c_to_f(celsius):
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32
```

## Monitoring and Logging

All API interactions are logged for monitoring and debugging:

```python
def log_api_call(api_name, endpoint, params, success, response_data=None, error=None):
    """Log an API call for monitoring."""

    log_data = {
        "api": api_name,
        "endpoint": endpoint,
        "params": {k: v for k, v in params.items() if k not in ["appid", "key"]},  # Don't log API keys
        "success": success,
        "timestamp": datetime.now().isoformat()
    }

    if success and response_data:
        log_data["response_summary"] = summarize_response(response_data)

    if error:
        log_data["error"] = str(error)

    if success:
        logger.info("API call succeeded", extra=log_data)
    else:
        logger.error("API call failed", extra=log_data)
```

This comprehensive approach to API integration ensures reliable data retrieval, accurate verification, and proper error handling throughout the system.
