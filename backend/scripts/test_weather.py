
import sys
import os
sys.path.append('ingestion')
import weather_service
import json

lat = -27.8182
lng = 151.636
data = weather_service.fetch_weather(lat, lng)
formatted = weather_service.format_for_hamclock(data, lat, lng)
print(formatted)
