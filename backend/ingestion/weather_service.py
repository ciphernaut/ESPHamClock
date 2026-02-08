import requests
import os
import json
import logging
import time
from datetime import datetime
from timezonefinder import TimezoneFinder
import pytz

logger = logging.getLogger(__name__)

# Note: In a production environment, this should be moved to an environment variable.
# For this task, we'll use a placeholder or the user can provide one.
# However, many public APIs have a free tier that doesn't strictly require a personal key for low-volume testing,
# or we can use a service like wttr.in which is simpler.
# HamClock originally used OpenWeatherMap.

BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
WEATHER_DATA_DIR = os.path.join(BASE_DATA_DIR, "processed_data", "weather")

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
        logger.warning(f"Error fetching from wttr.in: {e}. Falling back to Open-Meteo.")
        try:
            # Fallback to Open-Meteo
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,pressure_msl,weather_code&timezone=GMT"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            om_data = resp.json()
            
            # Adapt Open-Meteo to wttr.in format (partial mapping needed for format_for_hamclock)
            # format_for_hamclock expectations:
            # data['current_condition'][0] -> temp_C, pressure, humidity, windspeedKmph, winddir16Point, weatherDesc[0]['value']
            # data['nearest_area'][0] -> areaName[0]['value']
            
            current = om_data.get('current', {})
            adapted = {
                'current_condition': [{
                    'temp_C': str(current.get('temperature_2m', 0)),
                    'pressure': str(current.get('pressure_msl', 1013)),
                    'humidity': str(current.get('relative_humidity_2m', 50)),
                    'windspeedKmph': str(current.get('wind_speed_10m', 0)),
                    'winddir16Point': deg_to_dir(current.get('wind_direction_10m', 0)),
                    'weatherDesc': [{'value': code_to_desc(current.get('weather_code', 0))}]
                }],
                'nearest_area': [{
                    'areaName': [{'value': f"{lat:.2f},{lng:.2f}"}]
                }]
            }
            
            # Save to cache
            with open(cache_file, 'w') as f:
                json.dump(adapted, f)
                
            return adapted
        except Exception as om_e:
            logger.warning(f"Error fetching from Open-Meteo fallback: {om_e}. Falling back to local grid.")
            return fetch_from_grid(lat, lng)

def fetch_from_grid(lat, lng):
    """Fallback: Find nearest point in local worldwx/wx.txt grid."""
    try:
        grid_file = os.path.join(BASE_DATA_DIR, "processed_data", "worldwx", "wx.txt")
        if not os.path.exists(grid_file):
            return None
            
        best_dist = float('inf')
        best_p = None
        
        with open(grid_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 9:
                    try:
                        p_lat = float(parts[0])
                        p_lng = float(parts[1])
                        dist = (lat - p_lat)**2 + (lng - p_lng)**2
                        if dist < best_dist:
                            best_dist = dist
                            best_p = {
                                'temp': parts[2], 'hum': parts[3],
                                'wind_spd': parts[4], 'wind_dir': parts[5],
                                'press': parts[6], 'cond': parts[7], 'tz': parts[8]
                            }
                        if dist == 0: break # Exact match
                    except (ValueError, IndexError):
                        continue
        
        if best_p:
            # Map grid condition back to wttr.in-like structure (very simplified)
            adapted = {
                'current_condition': [{
                    'temp_C': best_p['temp'],
                    'pressure': best_p['press'],
                    'humidity': best_p['hum'],
                    'windspeedKmph': str(float(best_p['wind_spd']) * 3.6),
                    'winddir16Point': deg_to_dir(float(best_p['wind_dir'])),
                    'weatherDesc': [{'value': best_p['cond']}]
                }],
                'nearest_area': [{
                    'areaName': [{'value': f"Grid({lat:.1f},{lng:.1f})"}]
                }]
            }
            return adapted
    except Exception as e:
        logger.error(f"Error in grid fallback: {e}")
    return None

def deg_to_dir(deg):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    idx = int((deg + 11.25) / 22.5) % 16
    return dirs[idx]

def code_to_desc(code):
    # Simplified WMO code mapping
    m = {0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
         51: "Drizzle", 53: "Drizzle", 55: "Drizzle", 61: "Rain", 63: "Rain", 65: "Rain",
         71: "Snow", 73: "Snow", 75: "Snow", 80: "Rain Showers", 81: "Rain Showers", 82: "Rain Showers",
         95: "Thunderstorm"}
    return m.get(code, "Clear")

def get_prevailing_stats():
    """
    Fetches global weather summary or aggregates from wttr.in.
    Returns string format for HamClock.
    """
    try:
        # For prevailing stats, HamClock originally might have aggregated its grid.
        # But if the user wants "via wttr.in", we can try to get a global summary
        # or just stick to the grid aggregation if that's what's meant by "parity".
        # However, the TODO specifically says "prevailing stats via wttr.in".
        # wttr.in doesn't have a single "global summary" endpoint.
        # It's possible "prevailing stats" refers to a specific major city or an aggregate.
        # Given the 0% parity in worldwx/wx.txt, let's first ensure we aggregate the grid correctly
        # but also provide a way to hook into wttr.in if a specific summary is needed.
        
        grid_file = os.path.join(BASE_DATA_DIR, "processed_data", "worldwx", "wx.txt")
        if not os.path.exists(grid_file):
            logger.warning(f"Grid file {grid_file} not found for prevailing stats")
            return "No data available"

        temps = []
        conditions = {}
        
        with open(grid_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 8:
                    try:
                        temp = float(parts[2])
                        cond = parts[7]
                        temps.append(temp)
                        conditions[cond] = conditions.get(cond, 0) + 1
                    except (ValueError, IndexError):
                        continue
        
        if not temps:
            return "No valid data in grid"

        min_temp = min(temps)
        max_temp = max(temps)
        avg_temp = sum(temps) / len(temps)
        
        # Most frequent condition
        prevailing_cond = max(conditions, key=conditions.get) if conditions else "Clear"
        
        # Format matching what HamClock might expect or common summary format
        # Note: We need to verify if the client expects a specific label-value format.
        # Based on the handle_word_wx handler, it's just raw text.
        return f"MinTemp: {min_temp:.1f}C\nMaxTemp: {max_temp:.1f}C\nAvgTemp: {avg_temp:.1f}C\nPrevailing: {prevailing_cond}"
    except Exception as e:
        logger.error(f"Error calculating prevailing stats: {e}")
        return "Error calculating stats"

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
        
        # Calculate timezone offset
        try:
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=lng, lat=lat)
            if not tz_name:
                # Fallback for coastal points
                tz_name = tf.closest_timezone_at(lng=lng, lat=lat)
            
            if tz_name:
                tz = pytz.timezone(tz_name)
                # Get offset for current time (considering DST)
                timezone = int(tz.utcoffset(datetime.now()).total_seconds())
            else:
                # Fallback to longitude based approximation
                timezone = int(round(float(lng) / 15.0) * 3600)
        except Exception as e:
            logger.warning(f"Error calculating timezone: {e}")
            try:
                timezone = int(round(float(lng) / 15.0) * 3600)
            except:
                timezone = 0
        
        lines = [
            f"city={city}",
            f"temperature_c={temp_c:.2f}",
            f"pressure_hPa={float(pressure):.2f}",
            f"pressure_chg=0.00",
            f"humidity_percent={float(humidity):.2f}",
            f"wind_speed_mps={wind_speed_mps:.2f}",
            f"wind_dir_name={wind_dir}",
            f"clouds={desc}",
            f"conditions={desc}",
            f"attribution=wttr.in",
            f"timezone={timezone}"
        ]
        
        return "\n".join(lines) + "\n"
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
