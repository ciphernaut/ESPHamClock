import requests
import os
import time
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Grid configuration
LAT_START, LAT_END, LAT_STEP = -90, 90, 4
LNG_START, LNG_END, LNG_STEP = -180, 180, 5

# Cache file to store weather points across runs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "data", "processed_data", "worldwx")
CACHE_FILE = os.path.join(CACHE_DIR, "grid_cache.json")
STATE_FILE = os.path.join(CACHE_DIR, "fetch_state.json")

def get_grid_coords():
    """Generate the list of coordinates for the HamClock weather grid."""
    coords = []
    # Original format is sorted by LNG then LAT
    for lng in range(LNG_START, LNG_END + 1, LNG_STEP):
        for lat in range(LAT_START, LAT_END + 1, LAT_STEP):
            coords.append((lat, lng))
    return coords

def map_wmo_to_hamclock(code):
    """Map Open-Meteo WMO weather codes to HamClock condition strings."""
    if code in [0, 1]:
        return "Clear"
    elif code in [2, 3, 45, 48]:
        return "Clouds"
    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]:
        return "Rain"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "Snow"
    return "Clear"

def fetch_batch_weather(coords_batch):
    """Fetch weather for a batch of coordinates from Open-Meteo."""
    lats = [str(c[0]) for c in coords_batch]
    lngs = [str(c[1]) for c in coords_batch]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": ",".join(lats),
        "longitude": ",".join(lngs),
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,pressure_msl,weather_code",
        "timezone": "auto"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            logger.error("429 Client Error: Too Many Requests for Open-Meteo. Throttling active.")
            return None
        resp.raise_for_status()
        data = resp.json()
        
        if isinstance(data, dict) and "current" in data:
            results = [data]
        else:
            results = data
            
        points = []
        for i, res in enumerate(results):
            current = res.get("current", {})
            lat, lng = coords_batch[i]
            
            temp = current.get("temperature_2m", 0)
            hum = current.get("relative_humidity_2m", 50)
            wind_speed = current.get("wind_speed_10m", 0) / 3.6 # km/h to m/s
            wind_dir = current.get("wind_direction_10m", 0)
            # Use hPa (msl) directly to match original server's behavior (client expects hPa)
            pressure = current.get("pressure_msl", 1013)
            condition = map_wmo_to_hamclock(current.get("weather_code", 0))
            # Use UTC offset from API if available, else fallback to naive
            tz_offset = res.get("utc_offset_seconds", int(round(lng / 15.0) * 3600))
            
            points.append({
                "lat": lat,
                "lng": lng,
                "temp": temp,
                "hum": hum,
                "wind_speed": wind_speed,
                "wind_dir": float(wind_dir),
                "pressure": pressure,
                "condition": condition,
                "tz": tz_offset,
                "updated": datetime.utcnow().isoformat()
            })
        return points
    except Exception as e:
        logger.error(f"Error fetching batch weather: {e}")
        return []

def load_cache():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def generate_weather_grid():
    """Generates wx.txt using cached data and refreshing a subset."""
    all_coords = get_grid_coords()
    cache = load_cache()
    
    # Identify which index to start from for this run
    start_idx = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                start_idx = json.load(f).get("next_idx", 0)
        except: pass
        
    if start_idx >= len(all_coords):
        start_idx = 0
        
    # Refresh a subset (1 batch of 50 = 50 points per 10 mins)
    # 3358 / 50 = 67 runs = ~11 hours to refresh entire world
    # 7,200 points per day (Limit 10,000)
    subset_size = 50
    batch_size = 50
    end_idx = min(start_idx + subset_size, len(all_coords))
    refresh_coords = all_coords[start_idx:end_idx]
    
    print(f"Refreshing weather grid subset: points {start_idx} to {end_idx}...")
    
    for i in range(0, len(refresh_coords), batch_size):
        batch = refresh_coords[i:i+batch_size]
        points = fetch_batch_weather(batch)
        if points is None:
            # 429 error encountered, stop further requests this run
            break
        if points:
            for p in points:
                key = f"{p['lat']},{p['lng']}"
                cache[key] = p
        time.sleep(2) # Be very nice to Open-Meteo
        
    save_cache(cache)
    
    # Update state for next run
    with open(STATE_FILE, 'w') as f:
        json.dump({"next_idx": end_idx if end_idx < len(all_coords) else 0}, f)
        
    # Generate wx.txt from cache
    lines = ["#   lat     lng  temp,C     %hum    mps     dir    mmHg    Wx           TZ"]
    
    current_lng = -180
    for lat, lng in all_coords:
        key = f"{lat},{lng}"
        p = cache.get(key)
        
        # Placeholder for points not yet in cache
        if not p:
            p = {
                "lat": lat, "lng": lng, "temp": 0.0, "hum": 50.0,
                "wind_speed": 0.0, "wind_dir": 0.0, "pressure": 1013.0,
                "condition": "Clear", "tz": int(round(lng / 15.0) * 3600)
            }
            
        if lng != current_lng:
            lines.append("")
            current_lng = lng
            
        line = f"{p['lat']:>7} {p['lng']:>7} {p['temp']:>7.1f} {p['hum']:>7.1f} {p['wind_speed']:>7.1f} {p['wind_dir']:>7.1f} {p['pressure']:>7.1f} {p['condition']:<12} {p['tz']:>7}"
        lines.append(line)
        
    grid_str = "\n".join(lines) + "\n"
    
    # Write to file
    grid_file = os.path.join(CACHE_DIR, "wx.txt")
    try:
        with open(grid_file, 'w') as f:
            f.write(grid_str)
        logger.info(f"Successfully updated weather grid: {grid_file}")
    except Exception as e:
        logger.error(f"Error writing grid file: {e}")
        
    return grid_str

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    grid = generate_weather_grid()
    print(grid[:500])
    print(f"Total lines: {len(grid.splitlines())}")
