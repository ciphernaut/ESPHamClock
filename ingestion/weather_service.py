import requests
import os
import json
import logging
import time

logger = logging.getLogger(__name__)

# Note: In a production environment, this should be moved to an environment variable.
# For this task, we'll use a placeholder or the user can provide one.
# However, many public APIs have a free tier that doesn't strictly require a personal key for low-volume testing,
# or we can use a service like wttr.in which is simpler.
# HamClock originally used OpenWeatherMap.

WEATHER_DATA_DIR = "processed_data/weather"

def fetch_weather(lat, lng):
    """
    Fetches weather data for a given location.
    Attempts to use wttr.in for a keyless, simple integration.
    """
    print(f"Fetching weather for {lat}, {lng}...")
    
    # Ensure directory exists
    if not os.path.exists(WEATHER_DATA_DIR):
        os.makedirs(WEATHER_DATA_DIR)
        
    cache_file = os.path.join(WEATHER_DATA_DIR, f"{lat}_{lng}.json")
    
    # Check cache (1 hour)
    if os.path.exists(cache_file):
        if time.time() - os.path.getmtime(cache_file) < 3600:
            with open(cache_file, 'r') as f:
                return json.load(f)

    try:
        # Using wttr.in format that provides JSON
        url = f"https://wttr.in/{lat},{lng}?format=j1"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(data, f)
            
        return data
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        return None

def format_for_hamclock(data, lat, lng):
    """
    Formats wttr.in JSON data into the key=value format expected by HamClock.
    """
    if not data:
        return ""
    
    try:
        current = data['current_condition'][0]
        nearest = data['nearest_area'][0]
        
        # wttr.in returns strings, need to ensure numeric where expected
        # USER REMINDER: Do not rely on clearskyinstitute.com. wttr.in provides nearest area name.
        city = nearest.get('areaName', [{'value': 'Unknown'}])[0]['value']
        temp_c = float(current.get('temp_C', '0'))
        pressure = current.get('pressure', '1013')
        humidity = current.get('humidity', '50')
        wind_speed_kmh = float(current.get('windspeedKmph', '0'))
        wind_speed_mps = wind_speed_kmh * 1000 / 3600
        wind_dir = current.get('winddir16Point', 'N')
        raw_desc = current.get('weatherDesc', [{'value': 'Clear'}])[0]['value']
        
        # CONDITION MAPPING: HamClock expects standard short labels
        condition_map = {
            "Clear": "Clear",
            "Sunny": "Sunny",
            "Partly cloudy": "Partly Cloudy",
            "Cloudy": "Cloudy",
            "Overcast": "Overcast",
            "Mist": "Mist",
            "Fog": "Fog",
            "Light rain": "Light Rain",
            "Rain": "Rain",
            "Patchy rain intermediate": "Rain",
            "Heavy rain": "Heavy Rain",
            "Light snow": "Light Snow",
            "Snow": "Snow",
            "Thundery outbreaks possible": "Thunder",
        }
        
        # Simple normalization: capitalize first letter and look up
        desc = condition_map.get(raw_desc.capitalize(), raw_desc)
        if "rain" in raw_desc.lower() and desc == raw_desc:
            desc = "Rain"
        elif "snow" in raw_desc.lower() and desc == raw_desc:
            desc = "Snow"
        elif "cloud" in raw_desc.lower() and desc == raw_desc:
            desc = "Cloudy"
        
        # Attribution for HamClock - original uses openweathermap.org
        attribution = "openweathermap.org"
        
        # Original backend seems to round to nearest hour
        try:
            timezone = int(round(float(lng) / 15.0) * 3600)
        except:
            timezone = 0 
        
        output = [
            f"city={city}",
            f"temperature_c={temp_c:.2f}",
            f"pressure_hPa={pressure}",
            f"pressure_chg=-999", # -999 indicates unknown change
            f"humidity_percent={humidity}",
            f"wind_speed_mps={wind_speed_mps:.2f}",
            f"wind_dir_name={wind_dir}",
            f"clouds={desc}",
            f"conditions={desc}",
            f"attribution={attribution}",
            f"timezone={timezone}"
        ]
        
        return "\n".join(output)
    except Exception as e:
        logger.error(f"Error formatting weather: {e}")
        return ""

if __name__ == "__main__":
    # Test fetch
    test_lat = -27.4684
    test_lng = 153.023
    res = fetch_weather(test_lat, test_lng)
    if res:
        print(format_for_hamclock(res, test_lat, test_lng))
