
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
sys.path.append(os.path.join(os.getcwd(), 'backend/ingestion'))

import weather_service
import time
import logging

logging.basicConfig(level=logging.DEBUG)

def stress_test():
    coords = [
        (-27.0, 152.0),
        (40.7, -74.0),
        (51.5, -0.1),
        (35.6, 139.7),
        (62.7, -92.1) # The one from logs
    ]
    
    for i in range(20):
        print(f"Iteration {i}")
        for lat, lng in coords:
            print(f"Fetching {lat}, {lng}")
            try:
                wb = weather_service.fetch_weather(lat, lng)
                # print(wb)
                res = weather_service.format_for_hamclock(wb, lat, lng)
                print(f"Result len: {len(res)}")
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(0.5)

if __name__ == "__main__":
    stress_test()
