import requests
import os
import json
import logging
import time
import datetime
import re
try:
    from ingestion import onta_service, dxped_service, drap_service, weather_grid_service
except ImportError:
    import onta_service, dxped_service, drap_service, weather_grid_service

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
# Kyoto WDC Dst source
KYOTO_DST_BASE_URL = "http://wdc.kugi.kyoto-u.ac.jp/dst_realtime"
DRAP_URL = "https://services.swpc.noaa.gov/json/drap_absorption_stats.json"
WORLD_WX_URL = "https://clearskyinstitute.com/ham/HamClock/worldwx/wx.txt"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed_data")

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
        
        date_str = f"{year} {month.zfill(2)} {day.zfill(2)}"
        ssn_records.append(f"{date_str} {ssn}")
        # Add 3 records per day for solar flux to reach 99 values for 33 days (SFLUX_NV)
        flux_records.extend([sw_flux, sw_flux, sw_flux])

    # Save SSN (last 31 days)
    # Ensure we have at least 31 records and take the most recent ones.
    # HamClock usually shows the current month clearly.
    ssn_file = os.path.join(OUTPUT_DIR, "ssn", "ssn-31.txt")
    with open(ssn_file, "w") as f:
        # Pad if we have less than 31
        final_ssn = ssn_records
        while len(final_ssn) < 31:
            final_ssn.insert(0, final_ssn[0] if final_ssn else "0")
        
        for record in final_ssn[-31:]:
            f.write(f"{record}\n")
    print(f"Saved {len(final_ssn[-31:])} SSN records to {ssn_file}")

    # Save Solar Flux (last 99 values - matching SFLUX_NV)
    # Original expects 3 samples per day for 33 days.
    flux_file = os.path.join(OUTPUT_DIR, "solar-flux", "solarflux-99.txt")
    with open(flux_file, "w") as f:
        # If we have less than 99, pad by repeating oldest
        final_flux = flux_records
        while len(final_flux) < 99:
            final_flux.insert(0, final_flux[0] if final_flux else "0")
        
        for record in final_flux[-99:]:
            f.write(f"{record}\n")
    print(f"Saved {len(final_flux[-99:])} flux records to {flux_file}")

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
                match = re.search(r'(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$', line)
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
                    # We take only the first two days of predictions (Day 1, Day 2)
                    try:
                        kp_predicted.append((float(parts[1]), float(parts[2])))
                    except ValueError: pass
        
        # kp_predicted is currently [(UT0_D1, UT0_D2), (UT1_D1, UT1_D2), ...]
        # We need to flatten it: D1_UT0, D1_UT1, ..., D1_UT7, D2_UT0, ...
        day1 = [p[0] for p in kp_predicted]
        day2 = [p[1] for p in kp_predicted]
        kp_predicted = day1[:8] + day2[:8] # Ensure exactly 8 per day
    except Exception as e:
        print(f"Error fetching predicted KP: {e}")

    # Combine: last 56 historical (7 days) + 16 predicted (2 days)
    total_kp = kp_history[-56:] + kp_predicted[:16]
    
    # Force exactly 72 values
    if len(total_kp) > 72:
        total_kp = total_kp[-72:] # Keep the most recent 72
    elif len(total_kp) < 72:
        print(f"Warning: Only found {len(total_kp)} KP values (need 72). Padding...")
        while len(total_kp) < 72:
            total_kp.append(total_kp[-1] if total_kp else 0.0)

    kp_file = os.path.join(OUTPUT_DIR, "geomag", "kindex.txt")
    with open(kp_file, "w") as f:
        for val in total_kp:
            f.write(f"{val:.2f}\n")
    print(f"Saved {len(total_kp)} KP records to {kp_file}")

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
            # HamClock samples at 10-min intervals ending in 5
            if dt.minute % 10 != 5:
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
            # Format: 2026  2  1  1105   00000  00000     1.99e-06    1.72e-05
            # Note: 2 spaces between year/month/day/time.
            parts = k.split() # YYYY MM DD HHMM
            # The original has a very specific space alignment:
            # 2026  2  1  1232
            # 0-3: year, 4-5: spaces, 6: month(1), 7-8: spaces, 9: day(1), 10-11: spaces, 12-15: time(4)
            # If month is 2 digits, it likely takes pos 5-6.
            formatted = f"{parts[0]:4} {int(parts[1]):>2} {int(parts[2]):>2}  {parts[3]:04}   00000  00000     {s_val:8.2e}    {l_val:8.2e}"
            records.append(formatted)
        
        xray_file = os.path.join(OUTPUT_DIR, "xray", "xray.txt")
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
        
        plasma_json = plasma_resp.json()
        mag_json = mag_resp.json()
        
        plasma_data = {e[0]: e for e in plasma_json[1:]} # time_tag: record
        mag_data = {e[0]: e for e in mag_json[1:]}
        
        # Pre-calculate UTS for all available times
        all_times = sorted(set(plasma_data.keys()) | set(mag_data.keys()))
        uts_map = {}
        for t_str in all_times:
            try:
                # 2026-02-02 23:25:00.000
                dt = datetime.datetime.strptime(t_str.replace('Z', ''), "%Y-%m-%d %H:%M:%S.%f")
                uts_map[t_str] = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
            except: pass
        
        # Last point timestamped at a 60-second boundary
        now_ts = (int(time.time()) // 60) * 60
        sorted_times = sorted(uts_map.items(), key=lambda x: x[1])

        # 1. Solar Wind (1440 points for 24h, 1-min interval)
        swind_final = []
        for i in range(1440):
            target_ts = now_ts - (1439 - i) * 60
            closest_t = None
            min_diff = 31 
            # Linear search is fine for 1300 items
            for t_str, t_uts in sorted_times:
                diff = abs(t_uts - target_ts)
                if diff < min_diff:
                    min_diff = diff
                    closest_t = t_str
            
            if closest_t:
                p = plasma_data.get(closest_t)
                if p and p[1] is not None and p[2] is not None:
                    # Density rounding: strip trailing .0
                    d_val = float(p[1])
                    d_str = f"{d_val:.2f}".rstrip('0').rstrip('.')
                    # Speed rounding: strip trailing .0
                    s_val = float(p[2])
                    s_str = f"{s_val:.1f}".rstrip('0').rstrip('.')
                    swind_final.append(f"{target_ts} {d_str} {s_str}")
                else:
                    swind_final.append(f"{target_ts} 0.00 0.0") # Padding
            else:
                swind_final.append(f"{target_ts} 0.00 0.0")

        # 2. Bz (150 points, 10-min interval)
        bz_final = []
        for i in range(150):
            target_ts = now_ts - (149 - i) * 600
            closest_t = None
            min_diff = 301
            for t_str, t_uts in sorted_times:
                diff = abs(t_uts - target_ts)
                if diff < min_diff:
                    min_diff = diff
                    closest_t = t_str
            
            if closest_t:
                m = mag_data.get(closest_t)
                if m and m[1] is not None and m[2] is not None and m[3] is not None and m[6] is not None:
                    # Spacing: UNIX(10) + 3 + Bx(4) + 3 + By(4) + 3 + Bz(4) + 4 + Bt(4)
                    # Precision: .1f
                    bz_final.append(f"{target_ts}   {float(m[1]):>4.1f}   {float(m[2]):>4.1f}   {float(m[3]):>4.1f}    {float(m[6]):>4.1f}")
                else:
                    bz_final.append(f"{target_ts}    0.0   0.0   0.0    0.0")
            else:
                bz_final.append(f"{target_ts}    0.0   0.0   0.0    0.0")

        # Write files
        sw_dir = os.path.join(OUTPUT_DIR, "solar-wind")
        if not os.path.exists(sw_dir): os.makedirs(sw_dir)
        swind_file = os.path.join(sw_dir, "swind-24hr.txt")
        with open(swind_file, "w") as f:
            for r in swind_final:
                f.write(f"{r}\n")
        
        bz_dir = os.path.join(OUTPUT_DIR, "Bz")
        if not os.path.exists(bz_dir): os.makedirs(bz_dir)
        bz_file = os.path.join(bz_dir, "Bz.txt")
        with open(bz_file, "w") as f:
            f.write("# UNIX        Bx     By     Bz     Bt\n")
            for r in bz_final:
                f.write(f"{r}\n")
        
        print(f"Saved {len(swind_final)} SWind and {len(bz_final)} Bz records.")
    except Exception as e:
        print(f"Error fetching Solar Wind/Mag: {e}")
        import traceback
        traceback.print_exc()

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
        
        scales_file = os.path.join(OUTPUT_DIR, "NOAASpaceWX", "noaaswx.txt")
        with open(scales_file, "w") as f:
            # exact spacing for parity
            f.write(f"R  {r} 0 0 0\n")
            f.write(f"S  {s} 0 0 0\n")
            f.write(f"G  {g} 0 0 0\n")
            
        print(f"Saved NOAA scales to {scales_file}")
        
        # Add rank2_coeffs.txt - original has it, we should too
        rank_file = os.path.join(OUTPUT_DIR, "NOAASpaceWX", "rank2_coeffs.txt")
        if not os.path.exists(rank_file):
            with open(rank_file, "w") as f:
                f.write("# index a b c\n")
                for i in range(10):
                    f.write(f"{i} 0 1 0\n")
    except Exception as e:
        print(f"Error fetching NOAA scales: {e}")

def fetch_aurora():
    """Fetch Aurora probability and maintain history"""
    print(f"Fetching Aurora from {AURORA_URL}...")
    try:
        resp = requests.get(AURORA_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        ts = data.get('Forecast Time', datetime.datetime.now(datetime.timezone.utc).isoformat())
        max_prob = 0
        coords = data.get('coordinates', [])
        if coords:
            probs = [c[2] for c in coords]
            max_prob = max(probs) if probs else 0
            
        aurora_dir = os.path.join(OUTPUT_DIR, "aurora")
        if not os.path.exists(aurora_dir):
            os.makedirs(aurora_dir)
        aurora_file = os.path.join(aurora_dir, "aurora.txt")
        
        # Load existing
        history = {}
        if os.path.exists(aurora_file):
            with open(aurora_file, "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        history[int(parts[0])] = parts[1]
                        
        # Current
        try:
            dt = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
            uts = int(dt.timestamp())
        except:
            uts = int(time.time())

        # HamClock check: if age of top sample is > 1.0 hr, it says "arora data invalid"
        # So we use the current UTS precisely.
        history[uts] = str(int(max_prob))
        
        # Sort and limit to last 48 points (AURORA_MAXPTS)
        sorted_uts = sorted(history.keys())
        # To avoid "arora data invalid" on first run, we pad if too short
        if len(sorted_uts) < 10:
            for i in range(10 - len(sorted_uts)):
                fake_uts = sorted_uts[0] - (i + 1) * 1800 # 30 min intervals
                history[fake_uts] = "0"
            sorted_uts = sorted(history.keys())
            
        # Keep last 48 points
        recent_uts = sorted_uts[-48:]
        
        with open(aurora_file, "w") as f:
            for u in recent_uts:
                f.write(f"{u} {history[u]}\n")
        print(f"Updated Aurora history with {len(recent_uts)} points")
    except Exception as e:
        print(f"Error fetching Aurora: {e}")

def fetch_onta():
    """Fetch live ONTA spots via onta_service"""
    print("Fetching live ONTA spots...")
    try:
        data = onta_service.get_onta_data()
        onta_dir = os.path.join(OUTPUT_DIR, "ONTA")
        if not os.path.exists(onta_dir):
            os.makedirs(onta_dir)
        with open(os.path.join(onta_dir, "onta.txt"), "w") as f:
            f.write(data)
        print("Updated ONTA/onta.txt with live spots")
    except Exception as e:
        print(f"Error updating ONTA: {e}")

def fetch_dxpeds():
    """Fetch live DXPeditions via dxped_service"""
    print("Fetching live DXPeditions...")
    try:
        data = dxped_service.get_dxped_data()
        dxped_dir = os.path.join(OUTPUT_DIR, "dxpeds")
        if not os.path.exists(dxped_dir):
            os.makedirs(dxped_dir)
        # Note: HamClock looks for both dxpeds/dxpeditions.txt and processed_data/dxpeditions.txt 
        # based on server.py routing.
        with open(os.path.join(OUTPUT_DIR, "dxpeditions.txt"), "w") as f:
            f.write(data)
        with open(os.path.join(dxped_dir, "dxpeditions.txt"), "w") as f:
            f.write(data)
        print("Updated dxpeditions.txt with live data")
    except Exception as e:
        print(f"Error updating DXPeditions: {e}")
def fetch_dst():
    """Fetch Disturbance Storm Time (Dst) index from Kyoto WDC and format for HamClock"""
    now = datetime.datetime.now(datetime.timezone.utc)
    yymm = now.strftime("%y%m")
    yyyymm = now.strftime("%Y%m")
    
    # Try current month first
    url = f"{KYOTO_DST_BASE_URL}/presentmonth/dst{yymm}.for.request"
    print(f"Fetching Dst index from {url}...")
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            # Try specific month folder as fallback
            url = f"{KYOTO_DST_BASE_URL}/{yyyymm}/dst{yymm}.for.request"
            print(f"Retrying Dst from {url}...")
            resp = requests.get(url, timeout=15)
        
        resp.raise_for_status()
        lines = resp.text.splitlines()
        
        # Kyoto format: 120-byte records
        # Columns 21-116: 24 hourly values (4-digit integers)
        # Missing: 9999
        dst_values = []
        for line in lines:
            if not line.startswith('DST'): continue
            try:
                year_short = int(line[3:5])
                month = int(line[5:7])
                day = int(line[8:10])
                year_long = int(line[14:16]) * 100 + year_short
                
                # Hourly data starts at index 20 (0-indexed)
                hourly_part = line[20:116]
                for h in range(24):
                    val_str = hourly_part[h*4 : (h+1)*4].strip()
                    if val_str and val_str != '9999':
                        ts = datetime.datetime(year_long, month, day, h, 0, 0, tzinfo=datetime.timezone.utc)
                        dst_values.append((ts, int(val_str)))
            except (ValueError, IndexError):
                continue
        
        if not dst_values:
            raise ValueError("No valid Dst records parsed")
            
        # Sort by time and take last 24 records (HamClock typically expects ~24-48 hours)
        dst_values.sort(key=lambda x: x[0])
        
        dst_dir = os.path.join(OUTPUT_DIR, "dst")
        if not os.path.exists(dst_dir): os.makedirs(dst_dir)
        dst_file = os.path.join(dst_dir, "dst.txt")
        
        with open(dst_file, "w") as f:
            for ts, val in dst_values[-24:]:
                # Format: 2026-02-01T03:00:00 0
                f.write(f"{ts.strftime('%Y-%m-%dT%H:%M:%S')} {val}\n")
                
        print(f"Saved {len(dst_values[-24:])} Dst records to {dst_file}")
        
    except Exception as e:
        print(f"Error fetching Dst from Kyoto: {e}. Checking for fallback...")
        dst_dir = os.path.join(OUTPUT_DIR, "dst")
        dst_file = os.path.join(dst_dir, "dst.txt")
        if not os.path.exists(dst_file):
            # Create minimal dummy data to prevent client crash
            now = datetime.datetime.now(datetime.timezone.utc)
            with open(dst_file, "w") as f:
                for h in range(24):
                    ts = now - datetime.timedelta(hours=23-h)
                    ts = ts.replace(minute=0, second=0, microsecond=0)
                    f.write(f"{ts.strftime('%Y-%m-%dT%H:%M:%S')} 0\n")
            print("Created dummy Dst data as fallback")

def fetch_static_file(url, filename):
    """Fetch a static file and save it to the output directory"""
    print(f"Fetching static file from {url}...")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        filepath = os.path.join(OUTPUT_DIR, filename)
        # Ensure directory exists for the static file
        file_dir = os.path.dirname(filepath)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"Saved {filename}")
    except Exception as e:
        print(f"Error fetching {filename}: {e}")

def fetch_all():
    """Run all fetchers and update local data files"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Ensure all required subdirectories exist
    subdirs = ["ssn", "solar-flux", "geomag", "xray", "solar-wind", "Bz", 
               "aurora", "NOAASpaceWX", "drap", "cty", "ONTA", "dxpeds", "contests", "dst", "worldwx"]
    for sd in subdirs:
        path = os.path.join(OUTPUT_DIR, sd)
        if not os.path.exists(path):
            os.makedirs(path)

    fetch_and_parse_solar_indices()
    fetch_and_parse_kp()
    fetch_xray()
    fetch_solar_wind_and_bz()
    fetch_noaa_scales()
    fetch_aurora()
    fetch_onta()
    fetch_dxpeds()
    fetch_dst()
    
    # Update DRAP (New dynamic service)
    print("Fetching DRAP absorption data...")
    try:
        drap_service.fetch_and_process_drap()
    except Exception as e:
        print(f"Error updating DRAP: {e}")
    
    # Fetch additional static resources into specific paths
    # fetch_static_file(DRAP_URL, "drap/stats.txt") # Handled by drap_service.py now
    
    # Generate world weather grid locally
    print("Generating local world weather grid...")
    try:
        grid_data = weather_grid_service.generate_weather_grid()
        if grid_data:
            grid_file = os.path.join(OUTPUT_DIR, "worldwx", "wx.txt")
            with open(grid_file, "w") as f:
                f.write(grid_data)
            print("Successfully updated worldwx/wx.txt")
        else:
            print("Weather grid generation yielded no data, keeping existing file")
    except Exception as e:
        print(f"Error generating weather grid: {e}")

    fetch_static_file(DXCC_URL, "cty/cty_wt_mod-ll-dxcc.txt")
    # ONTA and DXPeds are now dynamic
    fetch_static_file(CONTESTS_URL, "contests/contests311.txt")

    print("\nFetch cycle complete.")

if __name__ == "__main__":
    fetch_all()
