# API Response Structure

This document details the structure of API responses from the weather data providers used in the Snowfall Alert System.

## OpenWeatherMap API

### One Call API Response Structure

This is the primary endpoint used for retrieving comprehensive weather data including current conditions, daily forecasts, and snowfall information.

**Endpoint:** `https://api.openweathermap.org/data/2.5/onecall`

**Example Response:**

```json
{
  "lat": 40.6514,
  "lon": -111.508,
  "timezone": "America/Denver",
  "timezone_offset": -25200,
  "current": {
    "dt": 1679420400,
    "sunrise": 1679403247,
    "sunset": 1679447433,
    "temp": 28.4,
    "feels_like": 19.6,
    "pressure": 1015,
    "humidity": 74,
    "dew_point": 21.0,
    "uvi": 3.41,
    "clouds": 90,
    "visibility": 10000,
    "wind_speed": 12.3,
    "wind_deg": 320,
    "weather": [
      {
        "id": 601,
        "main": "Snow",
        "description": "snow",
        "icon": "13d"
      }
    ],
    "snow": {
      "1h": 1.2
    }
  },
  "daily": [
    {
      "dt": 1679425200,
      "sunrise": 1679403247,
      "sunset": 1679447433,
      "moonrise": 1679408340,
      "moonset": 1679394060,
      "moon_phase": 0.02,
      "temp": {
        "day": 32.5,
        "min": 24.8,
        "max": 35.6,
        "night": 25.2,
        "eve": 30.4,
        "morn": 26.1
      },
      "feels_like": {
        "day": 24.3,
        "night": 18.0,
        "eve": 21.9,
        "morn": 17.5
      },
      "pressure": 1014,
      "humidity": 68,
      "dew_point": 20.3,
      "wind_speed": 15.7,
      "wind_deg": 315,
      "wind_gust": 27.5,
      "weather": [
        {
          "id": 601,
          "main": "Snow",
          "description": "snow",
          "icon": "13d"
        }
      ],
      "clouds": 95,
      "pop": 0.9,
      "snow": 8.5,
      "uvi": 3.8
    },
    {
      "dt": 1679511600,
      "sunrise": 1679489551,
      "sunset": 1679533895,
      "moonrise": 1679496300,
      "moonset": 1679486160,
      "moon_phase": 0.05,
      "temp": {
        "day": 35.2,
        "min": 22.3,
        "max": 39.7,
        "night": 27.1,
        "eve": 34.0,
        "morn": 23.5
      },
      "feels_like": {
        "day": 27.9,
        "night": 20.5,
        "eve": 27.0,
        "morn": 15.8
      },
      "pressure": 1019,
      "humidity": 61,
      "dew_point": 17.6,
      "wind_speed": 11.0,
      "wind_deg": 310,
      "wind_gust": 19.5,
      "weather": [
        {
          "id": 600,
          "main": "Snow",
          "description": "light snow",
          "icon": "13d"
        }
      ],
      "clouds": 75,
      "pop": 0.7,
      "snow": 2.5,
      "uvi": 4.2
    }
  ]
}
```

### Key Fields for Snowfall Data

- **`current.snow.1h`**: Snowfall amount for the last 1 hour in millimeters (if available)
- **`daily[0].snow`**: Snowfall amount for the current day in millimeters
- **`daily[1].snow`**: Snowfall amount for tomorrow in millimeters
- **`daily[0].weather[0].description`**: Text description of weather conditions
- **`daily[0].pop`**: Probability of precipitation (0-1)

### Error Response

```json
{
  "cod": 401,
  "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
}
```

## WeatherAPI.com

### Forecast API Response Structure

Used as a secondary source for verification of snowfall data.

**Endpoint:** `https://api.weatherapi.com/v1/forecast.json`

**Example Response:**

```json
{
  "location": {
    "name": "Park City",
    "region": "Utah",
    "country": "United States of America",
    "lat": 40.65,
    "lon": -111.51,
    "tz_id": "America/Denver",
    "localtime_epoch": 1679420480,
    "localtime": "2023-03-21 12:08"
  },
  "current": {
    "last_updated_epoch": 1679419800,
    "last_updated": "2023-03-21 12:00",
    "temp_c": -2.2,
    "temp_f": 28.0,
    "is_day": 1,
    "condition": {
      "text": "Light snow",
      "icon": "//cdn.weatherapi.com/weather/64x64/day/326.png",
      "code": 1213
    },
    "wind_mph": 12.5,
    "wind_kph": 20.2,
    "wind_degree": 320,
    "wind_dir": "NW",
    "pressure_mb": 1014.0,
    "pressure_in": 29.94,
    "precip_mm": 0.8,
    "precip_in": 0.03,
    "humidity": 75,
    "cloud": 90,
    "feelslike_c": -8.7,
    "feelslike_f": 16.3,
    "vis_km": 9.7,
    "vis_miles": 6.0,
    "uv": 3.0,
    "gust_mph": 20.4,
    "gust_kph": 32.8
  },
  "forecast": {
    "forecastday": [
      {
        "date": "2023-03-21",
        "date_epoch": 1679356800,
        "day": {
          "maxtemp_c": 2.0,
          "maxtemp_f": 35.6,
          "mintemp_c": -4.0,
          "mintemp_f": 24.8,
          "avgtemp_c": -1.1,
          "avgtemp_f": 30.0,
          "maxwind_mph": 15.7,
          "maxwind_kph": 25.2,
          "totalprecip_mm": 21.5,
          "totalprecip_in": 0.85,
          "totalsnow_cm": 21.6,
          "avgvis_km": 8.5,
          "avgvis_miles": 5.3,
          "avghumidity": 69,
          "daily_will_it_rain": 1,
          "daily_chance_of_rain": 95,
          "daily_will_it_snow": 1,
          "daily_chance_of_snow": 95,
          "condition": {
            "text": "Heavy snow",
            "icon": "//cdn.weatherapi.com/weather/64x64/day/338.png",
            "code": 1225
          },
          "uv": 3.0
        },
        "astro": {
          "sunrise": "07:14 AM",
          "sunset": "07:30 PM",
          "moonrise": "07:25 AM",
          "moonset": "08:14 PM",
          "moon_phase": "Waxing Crescent",
          "moon_illumination": "2"
        },
        "hour": [
          {
            "time_epoch": 1679382000,
            "time": "2023-03-21 01:00",
            "temp_c": -3.6,
            "temp_f": 25.5,
            "is_day": 0,
            "condition": {
              "text": "Light snow",
              "icon": "//cdn.weatherapi.com/weather/64x64/night/326.png",
              "code": 1213
            },
            "wind_mph": 9.2,
            "wind_kph": 14.8,
            "wind_degree": 312,
            "wind_dir": "NW",
            "pressure_mb": 1012.0,
            "pressure_in": 29.88,
            "precip_mm": 0.6,
            "precip_in": 0.02,
            "humidity": 85,
            "cloud": 95,
            "feelslike_c": -10.0,
            "feelslike_f": 14.0,
            "windchill_c": -10.0,
            "windchill_f": 14.0,
            "heatindex_c": -3.6,
            "heatindex_f": 25.5,
            "dewpoint_c": -5.6,
            "dewpoint_f": 21.9,
            "will_it_rain": 0,
            "chance_of_rain": 67,
            "will_it_snow": 1,
            "chance_of_snow": 85,
            "vis_km": 7.5,
            "vis_miles": 4.7,
            "gust_mph": 16.6,
            "gust_kph": 26.6,
            "uv": 1.0
          }
          // Additional hourly data omitted for brevity
        ]
      }
    ]
  }
}
```

### Key Fields for Snowfall Data

- **`forecast.forecastday[0].day.totalsnow_cm`**: Total snow for the day in centimeters
- **`forecast.forecastday[0].day.daily_will_it_snow`**: Binary indicator if snow is expected (0 or 1)
- **`forecast.forecastday[0].day.daily_chance_of_snow`**: Percentage chance of snow (0-100)
- **`forecast.forecastday[0].hour[X].chance_of_snow`**: Hourly chance of snow (0-100)
- **`current.condition.text`**: Text description of current weather conditions

### Error Response

```json
{
  "error": {
    "code": 1002,
    "message": "API key is invalid or not provided."
  }
}
```

## Processed Snow Data

After retrieving and processing API responses, the system creates standardized snow data objects for each resort, as shown below:

### OpenWeatherMap Processed Data

```json
{
  "resort": "Park City Mountain",
  "current_snow": 8.5,
  "forecast_snow": 2.5,
  "current_temp": 28.4,
  "conditions": "snow",
  "timestamp": "2023-03-21T12:10:45.123Z",
  "source": "OpenWeatherMap"
}
```

### WeatherAPI.com Processed Data

```json
{
  "resort": "Park City Mountain",
  "snow_cm": 21.6,
  "snow_inches": 8.5,
  "current_temp": 28.0,
  "conditions": "Light snow",
  "timestamp": "2023-03-21T12:11:13.456Z",
  "source": "WeatherAPI.com"
}
```

## Data Conversion

The system performs the following conversions when processing API responses:

- Centimeters to inches: `inches = cm / 2.54`
- Millimeters to inches: `inches = mm / 25.4`
- Celsius to Fahrenheit: `F = (C * 9/5) + 32`

## API Rate Limiting

Both APIs implement rate limiting that the system respects:

- **OpenWeatherMap**: 1,000 calls/day (free tier)
- **WeatherAPI.com**: 1,000,000 calls/month, maximum 1 call/second (free tier)

The system implements caching to reduce API calls and exponential backoff for retries on failures.
