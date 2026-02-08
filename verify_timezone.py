from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

def get_offset(lat, lng):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lng, lat=lat)
    if not tz_name:
        return None, None
    tz = pytz.timezone(tz_name)
    offset = tz.utcoffset(datetime.now()).total_seconds()
    return tz_name, offset

locations = [
    {"name": "India (New Delhi)", "lat": 28.6139, "lng": 77.2090, "expected_offset": 19800}, # +5:30
    {"name": "Adelaide", "lat": -34.9285, "lng": 138.6007, "expected_offset": 34200},   # +9:30 (standard) or +10:30 (DST depending on date)
    {"name": "London", "lat": 51.5074, "lng": -0.1278, "expected_offset": 0},           # +0
]

print("Verifying Timezones...")
for loc in locations:
    name, offset = get_offset(loc['lat'], loc['lng'])
    print(f"{loc['name']}: {name}, Offset: {offset} (Expected: {loc['expected_offset']} approx)")
