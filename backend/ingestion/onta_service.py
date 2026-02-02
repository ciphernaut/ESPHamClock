import requests
import json
import os
import datetime
import logging
import time

logger = logging.getLogger(__name__)

# Verified POTA API
POTA_URL = "https://api.pota.app/spot/activator"
# Verified SOTA API (api-db2 is newer)
SOTA_URL = "https://api-db2.sota.org.uk/api/spots/50"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_sota_spots():
    """Fetch recent SOTA spots"""
    try:
        resp = requests.get(SOTA_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        spots = []
        for s in data:
            try:
                call = s.get('activatorCallsign', s.get('callsign', 'Unknown'))
                freq_mhz = float(s.get('frequency', '0'))
                hz = int(freq_mhz * 1e6)
                ts_str = s.get('timeStamp', '')
                if not ts_str:
                    uts = int(time.time())
                else:
                    dt = datetime.datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    uts = int(dt.timestamp())
                
                mode = s.get('mode', 'CW')
                # SOTA summary lacks lat/lng. For now use 0,0 or lookup.
                # Since HamClock needs them, we might have to skip if 0,0 is not acceptable.
                # But original onta.txt has them.
                lat = 0.0
                lng = 0.0
                park = s.get('summitCode', 'Unknown')
                org = "SOTA"
                spots.append(f"{call},{hz},{uts},{mode},,{lat:.5f},{lng:.5f},{park},{org}")
            except Exception as e: pass
        return spots
    except Exception as e:
        logger.error(f"Error fetching SOTA: {e}")
        return []

def fetch_pota_spots():
    """Fetch recent POTA spots"""
    try:
        resp = requests.get(POTA_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        spots = []
        for s in data:
            try:
                call = s.get('activator', 'Unknown')
                # POTA 'frequency' is in KHz (e.g. "14185")
                freq_khz = float(s.get('frequency', '0'))
                hz = int(freq_khz * 1000)
                ts_str = s.get('spotTime', '')
                
                if 'T' in ts_str:
                    dt = datetime.datetime.fromisoformat(ts_str).replace(tzinfo=datetime.timezone.utc)
                else:
                    dt = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
                
                uts = int(dt.timestamp())
                mode = s.get('mode', 'CW')
                lat = float(s.get('latitude', 0.0))
                lng = float(s.get('longitude', 0.0))
                park = s.get('reference', 'Unknown')
                org = "POTA"
                spots.append(f"{call},{hz},{uts},{mode},,{lat:.5f},{lng:.5f},{park},{org}")
            except Exception as e: pass
        return spots
    except Exception as e:
        logger.error(f"Error fetching POTA: {e}")
        return []

def get_onta_data():
    """Aggregate all ONTA spots"""
    sota = fetch_sota_spots()
    pota = fetch_pota_spots()
    all_spots = sota + pota
    
    # Header
    result = ["#call,Hz,unix,mode,grid,lat,lng,park,org"]
    result.extend(all_spots)
    return "\n".join(result)

if __name__ == "__main__":
    print(get_onta_data())
