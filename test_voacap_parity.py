
import requests
import time
import sys

# Configuration
CLIENT1_BASE = "http://localhost:8001"
CLIENT2_BASE = "http://localhost:8002"
TIMEOUT = 5

# Fixed DE Location (VK4SHF HQ)
DE_LOC = {"grid": "QG63"}

# DX Locations to rotate through
DX_LOCS = [
    {"name": "London", "grid": "IO91WJ"},
    {"name": "Sydney", "grid": "QF56OD"},
    {"name": "Tokyo",  "grid": "PM95"},
    {"name": "Rio",    "grid": "GG87"},
]

def set_de(session, base_url, loc):
    """Sets the DE location using only grid and call."""
    try:
        # webserver.cpp: setWiFiNewDEDX_helper forbids mixing grid with lat/lng
        params = {
            "grid": loc["grid"]
        }
        print(f"[{base_url}] Setting DE to {loc['grid']})...")
        resp = session.get(f"{base_url}/set_newde", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        
        # Verify it stuck
        resp = session.get(f"{base_url}/get_de.txt", timeout=TIMEOUT)
        if resp.status_code == 200:
            print(f"   Current DE: {resp.text.strip()}")
        else:
            print(f"   WARNING: Could not verify DE (HTTP {resp.status_code})")
            
    except Exception as e:
        print(f"ERROR: Failed to set DE on {base_url}: {e}")
        sys.exit(1)

def set_dx(session, base_url, loc):
    """Sets the DX location using only grid."""
    try:
        params = {
            "grid": loc["grid"]
        }
        # print(f"[{base_url}] Setting DX to {loc['name']} ({loc['grid']})...")
        resp = session.get(f"{base_url}/set_newdx", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: Failed to set DX on {base_url}: {e}")

def get_voacap(session, base_url):
    """Fetches VOACAP text data."""
    try:
        resp = session.get(f"{base_url}/get_voacap.txt", timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.text.strip()
        return f"HTTP {resp.status_code}"
    except Exception as e:
        return f"ERROR: {e}"

def main():
    s = requests.Session()
    s.headers.update({'Connection': 'close'})

    print("--- Initializing DE Location (Grid Only) ---")
    set_de(s, CLIENT1_BASE, DE_LOC)
    set_de(s, CLIENT2_BASE, DE_LOC)
    print("DE Set. Starting DX Rotation Test...\n")

    for loc in DX_LOCS:
        print(f"--- Testing DX: {loc['name']} ({loc['grid']}) ---")
        
        set_dx(s, CLIENT1_BASE, loc)
        set_dx(s, CLIENT2_BASE, loc)
        
        # Wait for potential recalc
        time.sleep(3)
        
        out1 = get_voacap(s, CLIENT1_BASE)
        out2 = get_voacap(s, CLIENT2_BASE)
        
        def clean_lines(text):
            return [l for l in text.splitlines() if l.strip()]

        lines1 = clean_lines(out1)
        lines2 = clean_lines(out2)
        
        if lines1 == lines2:
            print(f"✅ MATCH ({len(lines1)} lines)")
        else:
            print(f"❌ MISMATCH")
            print(f"   Legacy (8002): {len(lines2)} lines")
            print(f"   Target (8001): {len(lines1)} lines")
            
            max_len = max(len(lines1), len(lines2))
            diff_count = 0
            for i in range(max_len):
                l1 = lines1[i] if i < len(lines1) else "<missing>"
                l2 = lines2[i] if i < len(lines2) else "<missing>"
                if l1 != l2:
                    diff_count += 1
                    if diff_count <= 5:
                        print(f"   Diff @ L{i+1}:")
                        print(f"     8001: {l1}")
                        print(f"     8002: {l2}")
            if diff_count > 5:
                print(f"   ... and {diff_count - 5} more differences.")
        
        print("")
        time.sleep(1)

if __name__ == "__main__":
    main()
