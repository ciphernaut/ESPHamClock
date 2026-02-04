import requests
import json

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": "-90",
    "longitude": "-180",
    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,pressure_msl,weather_code",
    "timezone": "GMT"
}

try:
    resp = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
