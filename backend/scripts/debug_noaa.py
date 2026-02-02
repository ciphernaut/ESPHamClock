import requests
import datetime

url = 'https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json'
r = requests.get(url)
data = r.json()
import time
with open('noaa_debug.txt', 'a') as f:
    f.write(f"Now: {int(time.time())}\n")
    dt = datetime.datetime.now(datetime.timezone.utc)
    f.write(f"Now UTC: {dt.isoformat()}\n")
    f.write(f"Now TS: {int(dt.timestamp())}\n")
