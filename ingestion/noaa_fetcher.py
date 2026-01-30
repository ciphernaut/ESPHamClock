import requests
import datetime
import os
import re

# NOAA SWPC endpoints
SOLAR_INDICES_URL = "https://services.swpc.noaa.gov/text/daily-solar-indices.txt"
GEO_INDICES_URL = "https://services.swpc.noaa.gov/text/daily-geomagnetic-indices.txt"
FORECAST_URL = "https://services.swpc.noaa.gov/text/3-day-forecast.txt"
XRAY_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
SW_PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
SW_MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json"
NOAA_SCALES_URL = "https://services.swpc.noaa.gov/products/noaa-scales.json"
# Note: Aurora is often derived from other data, but NOAA has a probability file.
# For simplicity, we'll fetch the ovation forecast or similar if possible.
AURORA_URL = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
DRAP_URL = "https://services.swpc.noaa.gov/text/drap_global_frequencies.txt"
DXCC_URL = "https://clearskyinstitute.com/ham/HamClock/cty/cty_wt_mod-ll-dxcc.txt"
ONTA_URL = "https://clearskyinstitute.com/ham/HamClock/ONTA/onta.txt"
DXPEDS_URL = "https://clearskyinstitute.com/ham/HamClock/dxpeds/dxpeditions.txt"
CONTESTS_URL = "https://clearskyinstitute.com/ham/HamClock/contests/contests311.txt"
DST_URL = "https://clearskyinstitute.com/ham/HamClock/dst/dst.txt"

OUTPUT_DIR = "processed_data"

def fetch_and_parse_solar_indices():
    """Fetch and format SSN and Solar Flux data"""
    print(f"Fetching solar indices from {SOLAR_INDICES_URL}...")
    try:
        resp = requests.get(SOLAR_INDICES_URL, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching solar indices: {e}")
        return

    lines = resp.text.splitlines()
    data_lines = [l for l in lines if not l.startswith(':') and not l.startswith('#')]
    
    ssn_records = []
    flux_records = []
    
    for line in data_lines:
        parts = line.split()
        if len(parts) < 10:
            continue
            
        year = parts[0]
        month = parts[1]
        day = parts[2]
        sw_flux = parts[3]
        ssn = parts[4]
        
        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        ssn_records.append(f"{date_str} {ssn}")
        flux_records.append(sw_flux)

    # Save SSN (last 31 days)
    ssn_file = os.path.join(OUTPUT_DIR, "ssn-31.txt")
    with open(ssn_file, "w") as f:
        for record in ssn_records[-31:]:
            f.write(f"{record}\n")
    print(f"Saved {len(ssn_records[-31:])} SSN records to {ssn_file}")

    # Save Solar Flux (last 99 values - matching SFLUX_NV)
    flux_file = os.path.join(OUTPUT_DIR, "solarflux-99.txt")
    with open(flux_file, "w") as f:
        for record in flux_records[-99:]:
            f.write(f"{record}\n")
    print(f"Saved {len(flux_records[-99:])} flux records to {flux_file}")

def fetch_and_parse_kp():
    """Fetch and format KP data (legacy /geomag/kindex.txt)
    Needs 7 days historical (56 values) + 2 days predicted (16 values) = 72 values.
    """
    print(f"Fetching historical KP from {GEO_INDICES_URL}...")
    kp_history = []
    try:
        resp = requests.get(GEO_INDICES_URL, timeout=10)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        for line in lines:
            if not line.startswith((':', '#')) and len(line) > 60:
                # Planetary K-indices are in the last columns
                # Example: 2026 01 01 ... 12   2.00  3.00  2.67  2.67  3.33  2.67  2.33  2.67
                match = re.search(r'(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)$', line)
                if match:
                    kp_history.extend([float(v) for v in match.groups()])
    except Exception as e:
        print(f"Error fetching historical KP: {e}")

    print(f"Fetching predicted KP from {FORECAST_URL}...")
    kp_predicted = []
    try:
        resp = requests.get(FORECAST_URL, timeout=10)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        in_kp_section = False
        for line in lines:
            if "NOAA Kp index breakdown" in line:
                in_kp_section = True
                continue
            if in_kp_section and "UT" in line:
                # 00-03UT       3.67         2.67         1.67
                parts = line.split()
                if len(parts) >= 4:
                    # We take only the first two days of predictions (Jan 30, Jan 31 in the example)
                    kp_predicted.append((float(parts[1]), float(parts[2])))
        
        # kp_predicted is currently [(UT0_D1, UT0_D2), (UT1_D1, UT1_D2), ...]
        # We need to flatten it: D1_UT0, D1_UT1, ..., D1_UT7, D2_UT0, ...
        day1 = [p[0] for p in kp_predicted]
        day2 = [p[1] for p in kp_predicted]
        kp_predicted = day1 + day2
    except Exception as e:
        print(f"Error fetching predicted KP: {e}")

    # Combine: last 56 historical (7 days) + 16 predicted (2 days)
    total_kp = kp_history[-56:] + kp_predicted[:16]
    
    if len(total_kp) < 72:
        print(f"Warning: Only found {len(total_kp)} KP values (need 72). Padding...")
        while len(total_kp) < 72:
            total_kp.append(total_kp[-1] if total_kp else 0.0)

    kp_file = os.path.join(OUTPUT_DIR, "kindex.txt")
    with open(kp_file, "w") as f:
        for val in total_kp[:72]:
            f.write(f"{val:.2f}\n")
    print(f"Saved 72 KP records to {kp_file}")

def fetch_xray():
    """Fetch X-Ray data and format it to match HamClock's expectation (10-min intervals)"""
    print(f"Fetching X-Ray from {XRAY_URL}...")
    try:
        resp = requests.get(XRAY_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # We need 0.05-0.4nm (short) and 0.1-0.8nm (long) flux
        # HamClock format: YYYY MM DD HHMM  00000  00000  flux_short  flux_long
        # Sample: 2026  1 29  0748   00000  00000     1.89e-08    6.82e-07
        
        short_flux = {}
        long_flux = {}
        
        for entry in data:
            time_tag = entry['time_tag'].replace('Z', '')
            # Parse YYYY-MM-DDTHH:MM:SS
            dt = datetime.datetime.strptime(time_tag, "%Y-%m-%dT%H:%M:%S")
            # We only keep rows where minute ends in 8 to match original 10-min sampling
            if dt.minute % 10 != 8:
                continue
                
            ts_key = dt.strftime("%Y %m %d %H%M")
            if entry.get('energy') == '0.05-0.4nm':
                short_flux[ts_key] = entry['flux']
            elif entry.get('energy') == '0.1-0.8nm':
                long_flux[ts_key] = entry['flux']
        
        # Merge and format
        records = []
        all_keys = sorted(list(set(short_flux.keys()) | set(long_flux.keys())))
        for k in all_keys:
            s_val = short_flux.get(k, 0.0)
            l_val = long_flux.get(k, 0.0)
            # Format: 2026  1 29  0748   00000  00000     1.89e-08    6.82e-07
            parts = k.split() # YYYY MM DD HHMM
            formatted = f"{parts[0]:>4} {int(parts[1]):>2} {int(parts[2]):>2}  {parts[3]:>4}   00000  00000    {s_val:8.2e}    {l_val:8.2e}"
            records.append(formatted)
        
        xray_file = os.path.join(OUTPUT_DIR, "xray.txt")
        # Keep approx 24-48 hours of 10-min data
        with open(xray_file, "w") as f:
            for record in records:
                f.write(f"{record}\n")
        print(f"Saved {len(records)} X-Ray records to {xray_file}")
    except Exception as e:
        print(f"Error fetching X-Ray: {e}")
        import traceback
        traceback.print_exc()

def fetch_solar_wind_and_bz():
    """Fetch Solar Wind (Plasma) and Bz/Bt (Mag) data"""
    print(f"Fetching Solar Wind and Mag data...")
    try:
        plasma_resp = requests.get(SW_PLASMA_URL, timeout=10)
        mag_resp = requests.get(SW_MAG_URL, timeout=10)
        plasma_resp.raise_for_status()
        mag_resp.raise_for_status()
        
        plasma_data = {e[0]: e for e in plasma_resp.json()[1:]} # time_tag: record
        mag_data = {e[0]: e for e in mag_resp.json()[1:]}
        
        # Merge by common time tags
        swind_records = []
        bz_records = []
        
        # Sort keys to ensure chronologic order
        all_times = sorted(set(plasma_data.keys()) | set(mag_data.keys()))
        
        for t in all_times:
            p = plasma_data.get(t)
            m = mag_data.get(t)
            
            # swind-24hr.txt format: utime : speed density temperature
            # bz.txt format: utime : bz bt
            
            # Convert ISO8601 to Unix timestamp if needed, but spacewx.cpp 
            # might handle it differently. Let's provide ISO8601 as seen in ssn-31.txt 
            # or custom for swind as per spacewx.cpp line 579: utime : min max mean
            # Wait, spacewx.cpp lines 1141-1150: crackISO8601 is used.
            
            # Actually, spacewx.cpp line 1097: sscanf (line, "%ld : %f %f %f", &utime, ...)
            # It expects Unix timestamp.
            
            ts = int(datetime.datetime.fromisoformat(t.replace('Z', '')).timestamp())
            
            if p:
                # density [1], speed [2], temperature [3]
                try:
                    swind_records.append(f"{ts} : {p[2]} {p[1]} {p[3]}")
                except (IndexError, ValueError): pass
            
            if m:
                # bz_gsm [3], bt [6]
                try:
                    bz_records.append(f"{ts} : {m[3]} {m[6]}")
                except (IndexError, ValueError): pass

        swind_file = os.path.join(OUTPUT_DIR, "swind-24hr.txt")
        with open(swind_file, "w") as f:
            for r in swind_records[-144:]: # Approx 24 hours of 10-min data
                f.write(f"{r}\n")
        
        bz_file = os.path.join(OUTPUT_DIR, "Bz.txt")
        with open(bz_file, "w") as f:
            for r in bz_records[-144:]:
                f.write(f"{r}\n")
        print(f"Saved Solar Wind and Bz records.")
    except Exception as e:
        print(f"Error fetching Solar Wind/Mag: {e}")

def fetch_noaa_scales():
    """Fetch current R, S, G scales"""
    print(f"Fetching NOAA scales...")
    try:
        resp = requests.get(NOAA_SCALES_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # data format: {"0": {"G": {"value": 0, ...}, "S": {...}, "R": {...}}, ...}
        # We want the current values
        current = data.get("0", {})
        r = current.get("R", {}).get("value", 0)
        s = current.get("S", {}).get("value", 0)
        g = current.get("G", {}).get("value", 0)
        
        scales_file = os.path.join(OUTPUT_DIR, "noaaswx.txt")
        with open(scales_file, "w") as f:
            f.write(f"R {r}\n")
            f.write(f"S {s}\n")
            f.write(f"G {g}\n")
        print(f"Saved NOAA scales to {scales_file}")
    except Exception as e:
        print(f"Error fetching NOAA scales: {e}")

def fetch_aurora():
    """Fetch Aurora probability"""
    # Spacewx.cpp expects ISO8601 timestamp and a probability
    # We'll use the ovation latest map and take a representative point or average
    print(f"Fetching Aurora from {AURORA_URL}...")
    try:
        resp = requests.get(AURORA_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Simplified: just take the max probability found in the map
        ts = data.get('Forecast Time', datetime.datetime.utcnow().isoformat())
        max_prob = 0
        coords = data.get('coordinates', [])
        if coords:
            # coords is a list of [lon, lat, prob]
            probs = [c[2] for c in coords]
            max_prob = max(probs) if probs else 0
            
        aurora_file = os.path.join(OUTPUT_DIR, "aurora.txt")
        with open(aurora_file, "w") as f:
            f.write(f"{ts.replace('Z', '')} {max_prob}\n")
        print(f"Saved Aurora data to {aurora_file}")
    except Exception as e:
        print(f"Error fetching Aurora: {e}")

def fetch_static_file(url, filename):
    """Fetch a static file and save it to the output directory"""
    print(f"Fetching static file from {url}...")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"Saved {filename}")
    except Exception as e:
        print(f"Error fetching {filename}: {e}")

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    fetch_and_parse_solar_indices()
    fetch_and_parse_kp()
    fetch_xray()
    fetch_solar_wind_and_bz()
    fetch_noaa_scales()
    fetch_aurora()
    
    # Fetch additional static resources
    fetch_static_file(DRAP_URL, "stats.txt")
    fetch_static_file(DXCC_URL, "cty_wt_mod-ll-dxcc.txt")
    fetch_static_file(ONTA_URL, "onta.txt")
    fetch_static_file(DXPEDS_URL, "dxpeditions.txt")
    fetch_static_file(CONTESTS_URL, "contests311.txt")
    fetch_static_file(DST_URL, "dst.txt")
