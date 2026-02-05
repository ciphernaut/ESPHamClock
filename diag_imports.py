import sys
import os

print("Check 1: Base imports")
import http.server
import socketserver
import urllib.parse
import logging
print("Base imports OK")

print("Check 2: Adding ingestion to path")
base_dir = os.getcwd()
ingestion_dir = os.path.join(base_dir, "backend", "ingestion")
sys.path.append(ingestion_dir)
print(f"Path: {sys.path[-1]}")

services = [
    "geoloc_service",
    "spot_service",
    "weather_service",
    "sdo_service",
    "drap_service",
    "voacap_service",
    "band_service"
]

for svc in services:
    print(f"Attempting to import {svc}...")
    try:
        mod = __import__(svc)
        print(f"Import {svc} OK")
    except Exception as e:
        print(f"IMPORT FAILED for {svc}: {e}")
        import traceback
        traceback.print_exc()

print("All diagnostic checks done.")
