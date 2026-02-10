import os
print("SCRIPT STARTING")
import sys
import zlib
import math
import struct
import requests
import json
import base64
from PIL import Image
import numpy as np

# Configuration
ORIGINAL_SERVER = "http://clearskyinstitute.com/ham/HamClock/fetchVOACAPArea.pl"
LOCAL_SERVER_URL = "http://localhost:9086/fetchVOACAPArea.pl"
LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
MODEL_ID = os.environ.get("LM_STUDIO_MODEL", "moondream2")

MAP_W = 660
MAP_H = 330
HEADER_SIZE = 122

def decode_bmp565(data, out_path):
    """
    Decodes RGB565 BMP data and saves as PNG.
    Expects data starting with 122 byte header.
    """
    if data.startswith(b'BM'):
        # Skip header
        pixels = np.frombuffer(data[HEADER_SIZE:], dtype=np.uint16)
        if len(pixels) != MAP_W * MAP_H:
            print(f"Warning: expected {MAP_W*MAP_H} pixels, got {len(pixels)}")
            pixels = pixels[:MAP_W * MAP_H]
        
        # Reshape to (H, W)
        pixels = pixels.reshape((MAP_H, MAP_W))
        
        # Extract RGB565: RRRRRGGGGGGBBBBB
        r = ((pixels >> 11) & 0x1F) << 3
        g = ((pixels >> 5) & 0x3F) << 2
        b = (pixels & 0x1F) << 3
        
        # Stack to RGB
        rgb = np.stack([r, g, b], axis=-1).astype(np.uint8)
        Image.fromarray(rgb).save(out_path)
        return True
    return False

def fetch_ground_truth(params):
    """Fetches ground truth from original server."""
    print(f"Fetching from original server for {params.get('MHZ')} MHz...")
    headers = {'User-Agent': 'HamClock-linux/4.22 (id 1301431275 up 510) crc 0'}
    try:
        resp = requests.get(ORIGINAL_SERVER, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.content
        print(f"Error: Server returned {resp.status_code}")
    except Exception as e:
        print(f"Fetch error: {e}")
    return None

def fetch_local(params):
    """Fetches from current local implementation."""
    print(f"Generating local map for {params.get('MHZ')} MHz...")
    try:
        resp = requests.get(LOCAL_SERVER_URL, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.content
        print(f"Error: Local server returned {resp.status_code}")
    except Exception as e:
        print(f"Local fetch error: {e}")
    return None

def decompress_dual_map(content):
    """Decompresses the dual-map response (Day/Night compressed BMPs)."""
    # The response is usually two Z-compressed chunks concatenated.
    # HamClock protocol uses X-2Z-lengths header to know the split, 
    # but we can try decompressing sequentially.
    try:
        # First chunk
        d = zlib.decompressobj()
        m1 = d.decompress(content)
        # Remaining is start of second chunk
        m2 = zlib.decompress(content[len(content) - len(d.unused_data):])
        return m1, m2
    except:
        # Fallback for simpler single-chunk if needed
        return zlib.decompress(content), None

def run_comparison(mhz=14.0):
    # Use raw string to match observed logs exactly
    full_url = f"{ORIGINAL_SERVER}?YEAR=2026&MONTH=2&UTC=12&TXLAT=45&TXLNG=-90&PATH=0&WATTS=100&WIDTH={MAP_W}&HEIGHT={MAP_H}&MHZ={mhz}&TOA=3.0&MODE=19&TOA=3.0"
    print(f"Requesting: {full_url}")
    
    # Ground Truth
    headers = {'User-Agent': 'HamClock-linux/4.22 (id 1301431275 up 510) crc 0'}
    try:
        resp = requests.get(full_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            gt_raw = resp.content
        else:
            print(f"Error: Server returned {resp.status_code}")
            return
    except Exception as e:
        print(f"Fetch error: {e}")
        return
    
    # Local
    local_raw = fetch_local({
        'YEAR': 2026, 'MONTH': 2, 'UTC': 12,
        'TXLAT': 45, 'TXLNG': -90,
        'PATH': 0, 'WATTS': 100,
        'WIDTH': MAP_W, 'HEIGHT': MAP_H,
        'MHZ': mhz, 'TOA': 3.0, 'MODE': 19
    })
    if not local_raw: return
    
    # Decompress and Convert
    m1_gt, m2_gt = decompress_dual_map(gt_raw)
    m1_loc, m2_loc = decompress_dual_map(local_raw)
    
    os.makedirs("refinement", exist_ok=True)
    decode_bmp565(m1_gt, "refinement/gt_day.png")
    decode_bmp565(m1_loc, "refinement/local_day.png")
    
    print("Files saved to refinement/ directory. Ready for analysis.")

if __name__ == "__main__":
    mhz = float(sys.argv[1]) if len(sys.argv) > 1 else 14.0
    run_comparison(mhz)
