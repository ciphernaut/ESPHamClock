import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend', 'ingestion'))

from weather_grid_service import get_grid_coords, TimezoneFinder, pytz, datetime

print("Testing Weather Grid Service Logic...")

# Test specific coordinates
test_coords = [
    (28.6139, 77.2090, "India"),
    (-34.9285, 138.6007, "Adelaide"),
    (51.5074, -0.1278, "London"),
    (8.0, 80.0, "Sri Lanka (Grid Point)")
]

tf = TimezoneFinder()

for lat, lng, name in test_coords:
    try:
        tz_name = tf.timezone_at(lng=lng, lat=lat)
        print(f"{name}: timezone_at({lat}, {lng}) -> {tz_name}")
        
        if not tz_name:
            tz_name = tf.closest_timezone_at(lng=lng, lat=lat)
            print(f"{name}: closest_timezone_at({lat}, {lng}) -> {tz_name}")

        if tz_name:
            tz = pytz.timezone(tz_name)
            offset = int(tz.utcoffset(datetime.now()).total_seconds())
            print(f"{name}: {tz_name} -> {offset} seconds")
        else:
            print(f"{name}: No timezone found")
    except Exception as e:
        print(f"{name}: Error {e}")
