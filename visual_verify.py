
import os
import shutil
import time
import requests
import subprocess
from datetime import datetime

# Configuration
# Client 1 (Shadow Proxy) is on Port 8001 (REST) / 8091 (RW)
# This client serves LOCAL backend data (with fallback), so it will show our changes.
CLIENT_REST_URL = "http://localhost:8001"
CLIENT_RW_URL = "http://localhost:8091" # For browser screenshot

DATA_DIR = "data/processed_data"
BACKUP_DIR = "data/backup_visual_verify"

def backup_data():
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    os.makedirs(BACKUP_DIR)
    
    # Backup relevant files
    for subdir in ["geomag", "Bz", "solar-wind"]:
        src = os.path.join(DATA_DIR, subdir)
        dst = os.path.join(BACKUP_DIR, subdir)
        if os.path.exists(src):
            shutil.copytree(src, dst)
    print(f"Backed up data to {BACKUP_DIR}")

def restore_data():
    for subdir in ["geomag", "Bz", "solar-wind"]:
        src = os.path.join(BACKUP_DIR, subdir)
        dst = os.path.join(DATA_DIR, subdir)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        if os.path.exists(src):
            shutil.copytree(src, dst)
    print("Restored original data.")

def write_space_wx(kp, bz, sw_speed):
    # 1. Kp Index
    kp_dir = os.path.join(DATA_DIR, "geomag")
    if not os.path.exists(kp_dir): os.makedirs(kp_dir)
    with open(os.path.join(kp_dir, "kindex.txt"), "w") as f:
        # Just write 56 lines of the value
        for _ in range(56):
            f.write(f"{kp:.1f}\n")
    
    # 2. Bz
    bz_dir = os.path.join(DATA_DIR, "Bz")
    if not os.path.exists(bz_dir): os.makedirs(bz_dir)
    with open(os.path.join(bz_dir, "Bz.txt"), "w") as f:
        # unix bx by bz bt
        now = int(time.time())
        f.write(f"{now} 0.0 0.0 {bz:.1f} 5.0\n")

    # 3. Solar Wind
    sw_dir = os.path.join(DATA_DIR, "solar-wind")
    if not os.path.exists(sw_dir): os.makedirs(sw_dir)
    with open(os.path.join(sw_dir, "swind-24hr.txt"), "w") as f:
        # unix density speed
        now = int(time.time())
        f.write(f"{now} 10.0 {sw_speed:.1f}\n")
    
    print(f"Injected Data: Kp={kp}, Bz={bz}, SW={sw_speed}")

def trigger_update_and_capture(label):
    print(f"Triggering update for {label}...")
    # Force VOACAP update by setting DE/DX or just refreshing
    # set_voacap doesn't exist as a direct endpoint usually, it's fetchVOACAP.pl
    # But to refresh the map, we can change the band or just wait.
    # Let's toggle the band to 40m (7MHz) to match our verification script
    # and then back or just capture 40m.
    
    # Command: set_band?band=40m
    try:
        # Ensure we are on 40m for best visibility of night path absorption
        requests.get(f"{CLIENT_REST_URL}/set_band?band=40m")
        time.sleep(2) 
        
        # Trigger map refresh (it might auto-refresh on band change)
        # We can also call fetchVOACAPArea.pl via backend but Client handles display.
        # Just wait a bit for Client to fetch new map.
        print("Waiting 10s for map render...")
        time.sleep(10)
        
        # Capture Screenshot using browser tool (handled by calling agent, 
        # but here we can just verify the backend served the map by hitting the URL ourselves?)
        # Actually, the user wants a screenshot. 
        # We will use the 'browser' tool in the next step. 
        # This script just sets the stage.
        print(f"Ready for {label} screenshot.")
        
    except Exception as e:
        print(f"Error triggering update: {e}")

def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "clean"
    
    if mode == "backup":
        backup_data()
    elif mode == "quiet":
        write_space_wx(kp=2.0, bz=2.0, sw_speed=350.0)
    elif mode == "storm":
        write_space_wx(kp=8.0, bz=-15.0, sw_speed=800.0)
    elif mode == "restore":
        restore_data()
    else:
        print("Usage: python3 visual_verify.py [backup|quiet|storm|restore]")

if __name__ == "__main__":
    main()
