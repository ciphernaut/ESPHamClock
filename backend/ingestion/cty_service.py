import requests
import os
import re
import datetime

CTY_WT_MOD_URL = "https://download.win-test.com/files/country/CTY_WT_MOD.DAT"
# Fallback if win-test is down
FALLBACK_URL = "https://www.country-files.com/cty/cty_wt_mod.dat"

# Calculate project root (assuming we are in backend/ingestion/cty_service.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "backend", "data", "processed_data", "cty")

def fetch_and_process_cty():
    """Download or use local CTY_WT_MOD.DAT and derive cty_wt_mod-ll-dxcc.txt"""
    content = None
    local_source = os.path.join(BASE_DIR, "CTY_WT_MOD.DAT")
    
    if os.path.exists(local_source):
        print(f"Using local CTY source: {local_source}")
        try:
            with open(local_source, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading local CTY source: {e}")

    if not content:
        print(f"Fetching CTY data from {CTY_WT_MOD_URL}...")
        headers = {'User-Agent': 'HamClock/1.0'}
        try:
            resp = requests.get(CTY_WT_MOD_URL, headers=headers, timeout=30)
            resp.raise_for_status()
            content = resp.text
        except Exception as e:
            print(f"Error fetching from primary URL: {e}")
            try:
                print(f"Trying fallback {FALLBACK_URL}...")
                resp = requests.get(FALLBACK_URL, headers=headers, timeout=30)
                resp.raise_for_status()
                content = resp.text
            except Exception as e2:
                print(f"Fallback failed: {e2}")
                return None

    if not content:
        return None

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    output_path = os.path.join(OUTPUT_DIR, "cty_wt_mod-ll-dxcc.txt")
    
    entities = []
    current_adif = None
    
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        # Parse ADIF from comment: # ADIF 246
        adif_match = re.search(r'# ADIF (\d+)', line)
        if adif_match:
            current_adif = adif_match.group(1)
            i += 1
            continue
            
        if line.startswith('#'):
            i += 1
            continue
            
        if line.endswith(':'):
            # Header line: Name: CQ: ITU: Continent: Lat: Long: TZ: PrimaryPrefix:
            # Example: Monaco: 14: 27: EU: 43.73: -7.40: -1.0: 3A:
            parts = [p.strip() for p in line.split(':')]
            if len(parts) >= 8:
                try:
                    lat = float(parts[4])
                    lng = float(parts[5])
                    # Convert Longitude: CTY.DAT uses West-positive, HamClock uses East-positive
                    lng = -lng 
                    
                    # Read prefix list (following lines until ;)
                    i += 1
                    prefix_data = ""
                    while i < len(lines):
                        p_line = lines[i].strip()
                        if p_line.startswith('#'):
                            i += 1
                            continue
                        prefix_data += p_line
                        if p_line.endswith(';'):
                            break
                        i += 1
                    
                    # Split prefix data by ,
                    prefix_data = prefix_data.rstrip(';')
                    for raw_p in prefix_data.split(','):
                        p = raw_p.strip()
                        if not p: continue
                        
                        # Handle overrides: PFX<LAT/LONG>
                        ovr_match = re.search(r'(.+)<([-+]?\d*\.?\d+)/([-+]?\d*\.?\d+).*>', p)
                        if ovr_match:
                            p_prefix = ovr_match.group(1)
                            p_lat = float(ovr_match.group(2))
                            p_lng = -float(ovr_match.group(3)) # Convert
                            
                            p_prefix = p_prefix.lstrip('=*')
                            entities.append((p_prefix, p_lat, p_lng, current_adif))
                        else:
                            p_prefix = p.lstrip('=*')
                            entities.append((p_prefix, lat, lng, current_adif))
                except (ValueError, IndexError):
                    pass
        i += 1
        
    # Write output
    try:
        with open(output_path, 'w') as f:
            now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S %Y')
            f.write(f"# extracted from CTY_WT_MOD.DAT on {now_str}Z\n")
            f.write("# prefix     lat+N   lng+E  DXCC\n")
            for p, lt, ln, adif in entities:
                # 1A           41.90   12.43  246
                f.write(f"{p:<12} {lt:7.2f} {ln:7.2f}  {adif}\n")
        print(f"Successfully generated {output_path} with {len(entities)} entries.")
        return output_path
    except Exception as e:
        print(f"Error writing output file: {e}")
        return None

if __name__ == "__main__":
    fetch_and_process_cty()
