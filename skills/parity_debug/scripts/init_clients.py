import sys
import requests
import argparse

def init_client(port, callsign, lat=None, lng=None):
    base_url = f"http://localhost:{port}"
    print(f"Initializing client on port {port} with callsign {callsign}...")
    
    # 1. Set Callsign
    try:
        url = f"{base_url}/set_newde?call={callsign}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print(f"  [OK] Callsign set to {callsign}")
        else:
            print(f"  [FAIL] Failed to set callsign: {r.status_code}")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # 2. Set Location if provided
    if lat is not None and lng is not None:
        try:
            url = f"{base_url}/set_newde?lat={lat}&lng={lng}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                print(f"  [OK] Location set to {lat}, {lng}")
            else:
                print(f"  [FAIL] Failed to set location: {r.status_code}")
        except Exception as e:
            print(f"  [ERROR] {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize HamClock clients via REST API.")
    parser.add_argument("--ports", nargs="+", type=int, default=[8001, 8002], help="REST ports of clients")
    parser.add_argument("--call", type=str, required=True, help="Callsign to set")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lng", type=float, help="Longitude")
    
    args = parser.parse_args()
    
    for port in args.ports:
        init_client(port, args.call, args.lat, args.lng)
