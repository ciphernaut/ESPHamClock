import requests
import sys

def get_geoloc(ip=None):
    """
    Look up geolocation for a given IP or the current machine.
    Uses ip-api.com (free for non-commercial use).
    """
    url = "http://ip-api.com/json/"
    if ip:
        url += ip
        
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data['status'] == 'fail':
            print(f"Error: {data['message']}")
            return None
            
        # Format for HamClock:
        # LAT=...
        # LNG=...
        # IP=...
        # CREDIT=...
        
        output = [
            f"LAT={data['lat']}",
            f"LNG={data['lon']}",
            f"IP={data['query']}",
            f"CREDIT=ip-api.com"
        ]
        return "\n".join(output)
        
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    ip_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = get_geoloc(ip_arg)
    if result:
        print(result)
