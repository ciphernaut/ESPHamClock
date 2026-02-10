import requests
import xml.etree.ElementTree as ET
import time
import sys
import logging
logger = logging.getLogger(__name__)

def fetch_pskreporter(callsign=None, grid=None, maxage_sec=1800, mode_filter=None, is_receiver=False):
    """
    Fetch spots from PSKReporter and format as HamClock CSV.
    Format: posting_time, de_grid, de_call, dx_grid, dx_call, mode, Hz, snr
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

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Fetching from {url} with {params} (attempt {attempt+1})...")
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 503 and attempt < max_retries:
                logger.warning("PSKReporter returned 503, retrying in 2s...")
                time.sleep(2)
                continue
            resp.raise_for_status()
            
            logger.debug(f"Received XML ({len(resp.text)} bytes): {resp.text[:200]}...")
            root = ET.fromstring(resp.text)
            spots = []
            
            all_reports = root.findall('receptionReport')
            logger.debug(f"Found {len(all_reports)} receptionReport elements")

            for report in all_reports:
                tx_call = report.get('senderCallsign')
                tx_grid = report.get('senderLocator', '')
                rx_call = report.get('receiverCallsign')
                rx_grid = report.get('receiverLocator', '')
                freq = report.get('frequency', '0')
                mode = report.get('mode', '')
                snr = report.get('sNR', '0')
                timestamp = report.get('flowStartSeconds', str(int(time.time())))
                
                # HamClock CSV: posting_time, de_grid, de_call, dx_grid, dx_call, mode, Hz, snr
                if is_receiver:
                    line = f"{timestamp},{rx_grid},{rx_call},{tx_grid},{tx_call},{mode},{freq},{snr}"
                else:
                    line = f"{timestamp},{tx_grid},{tx_call},{rx_grid},{rx_call},{mode},{freq},{snr}"
                spots.append(line)
                
            return "\n".join(spots)

        except Exception as e:
            logger.error(f"Error in PSKReporter request (attempt {attempt+1}): {e}")
            if attempt == max_retries:
                return f"Error: {e}"
            time.sleep(1)

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
