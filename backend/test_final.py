import requests
import json
import os
from ingestion import weather_grid_service

results = {}
try:
    pts = weather_grid_service.fetch_batch_weather([(0, 0)])
    results["manual_fetch"] = pts
except Exception as e:
    results["manual_fetch_error"] = str(e)

with open("final_diagnostic.json", "w") as f:
    json.dump(results, f, indent=2)
