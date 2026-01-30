import requests
import xml.etree.ElementTree as ET
import time
import sys

def fetch_pskreporter(callsign=None, grid=None, maxage_sec=1800, mode_filter=None, is_receiver=False):
    """
    Fetch spots from PSKReporter and format as HamClock CSV.
    Format: posting_time, tx_grid, tx_call, rx_grid, rx_call, mode, Hz, snr
    """
    url = "https://retrieve.pskreporter.info/query"
    params = {
        "flowStartSeconds": -maxage_sec,
        "no_antennas": 1
    }
    
    if mode_filter:
        params["mode"] = mode_filter

    if callsign:
        if is_receiver:
            params["receiverCallsign"] = callsign
        else:
            params["senderCallsign"] = callsign
    elif grid:
        # PskReporter API primarily supports receiverGridSquare
        params["receiverGridSquare"] = grid
    else:
        return "Error: callsign or grid required"

    try:
        print(f"Fetching from {url} with {params}...", file=sys.stderr)
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        
        root = ET.fromstring(resp.text)
        spots = []
        
        # XML format: <receptionReport senderCallsign="..." senderLocator="..." receiverCallsign="..." receiverLocator="..." frequency="..." mode="..." reportID="..." flowStartSeconds="..." ... />
        for report in root.findall('receptionReport'):
            tx_call = report.get('senderCallsign')
            tx_grid = report.get('senderLocator', '')
            rx_call = report.get('receiverCallsign')
            rx_grid = report.get('receiverLocator', '')
            freq = report.get('frequency', '0')
            mode = report.get('mode', '')
            snr = report.get('snr', '0')
            timestamp = report.get('flowStartSeconds', str(int(time.time())))
            
            # HamClock CSV: posting_time, tx_grid, tx_call, rx_grid, rx_call, mode, Hz, snr
            line = f"{timestamp},{tx_grid},{tx_call},{rx_grid},{rx_call},{mode},{freq},{snr}"
            spots.append(line)
            
        return "\n".join(spots)

    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    # Test: python3 spot_service.py grid PM95 3600
    if len(sys.argv) < 3:
        print("Usage: python3 spot_service.py [call|grid] [value] [maxage_sec]")
    else:
        input_type = sys.argv[1]
        val = sys.argv[2]
        maxage = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
        
        if input_type == "call":
            print(fetch_pskreporter(callsign=val, maxage_sec=maxage))
        else:
            print(fetch_pskreporter(grid=val, maxage_sec=maxage))
