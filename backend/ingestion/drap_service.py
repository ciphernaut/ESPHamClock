import os
import requests
import logging
import time
import struct
import zlib
from PIL import Image

logger = logging.getLogger(__name__)

DRAP_DATA_URL = "https://services.swpc.noaa.gov/text/drap_global_frequencies.txt"
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_DIR = os.path.join(BASE_DATA_DIR, "processed_data", "drap")
STATS_FILE = os.path.join(DATA_DIR, "stats.history")
MAP_FILE = os.path.join(BASE_DATA_DIR, "processed_data", "map-D-DRAP.bmp")
MAP_FILE_Z = MAP_FILE + ".z"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    
maps_dir = os.path.join(BASE_DATA_DIR, "processed_data", "maps")
if not os.path.exists(maps_dir):
    os.makedirs(maps_dir)

def create_bmp_565_header(w, h):
    """
    Creates a 16bpp RGB565 BMP header (BITMAPV4HEADER) matching ESPHamClock requirements.
    h should be positive here; it will be negated in the header for top-down.
    """
    core_size = 14
    dib_size = 108
    hdr_len = core_size + dib_size
    
    # 16bpp aligned to 4 bytes per row
    row_bytes = ((16 * w + 31) // 32) * 4
    pix_bytes = row_bytes * h
    file_bytes = hdr_len + pix_bytes
    
    # BITMAPFILEHEADER
    header = bytearray(b'BM')
    header += struct.pack('<L', file_bytes)    # size
    header += struct.pack('<H', 0)             # res1
    header += struct.pack('<H', 0)             # res2
    header += struct.pack('<L', hdr_len)       # offset
    
    # BITMAPV4HEADER
    header += struct.pack('<L', dib_size)      # size
    header += struct.pack('<l', w)             # width
    header += struct.pack('<l', -h)            # height (negative for top-down)
    header += struct.pack('<H', 1)             # planes
    header += struct.pack('<H', 16)            # bpp
    header += struct.pack('<L', 3)             # compression (BI_BITFIELDS)
    header += struct.pack('<L', pix_bytes)     # image size
    header += struct.pack('<l', 0)             # hres
    header += struct.pack('<l', 0)             # vres
    header += struct.pack('<L', 0)             # ncolors
    header += struct.pack('<L', 0)             # nimportant
    
    # Masks
    header += struct.pack('<L', 0xF800)        # R mask
    header += struct.pack('<L', 0x07E0)        # G mask
    header += struct.pack('<L', 0x001F)        # B mask
    header += struct.pack('<L', 0x0000)        # A mask
    
    header += struct.pack('<L', 1)             # CSType (LCS_sRGB)
    header += bytearray(36)                    # Endpoints (unused)
    header += struct.pack('<L', 0)             # Gamma Red
    header += struct.pack('<L', 0)             # Gamma Green
    header += struct.pack('<L', 0)             # Gamma Blue
    
    return header

def get_color_rgb565(v):
    # Simplified scale based on mapmanage.cpp d_scale
    if v <= 0: return 0
    # Map to RGB888 first then convert
    r, g, b = 0, 0, 0
    if v < 4:
        r, g, b = int(v/4*0x4E), int(v/4*0x13), int(v/4*0x8A)
    elif v < 9:
        r, g, b = 0, int((v-4)/5*0x1E), 0xFF
    elif v < 15:
        r, g, b = int((v-9)/6*0x78), 0xFB, 0xD6
    elif v < 20: r, g, b = 0x78, 0xFA, 0x4D
    elif v < 27: r, g, b = 0xFE, 0xFD, 0x54
    elif v < 30: r, g, b = 0xEC, 0x6F, 0x2D
    else: r, g, b = 0xE9, 0x33, 0x23
    
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def fetch_and_process_drap():
    try:
        logger.info(f"Fetching DRAP data from {DRAP_DATA_URL}")
        resp = requests.get(DRAP_DATA_URL, timeout=10)
        resp.raise_for_status()
        
        lines = resp.text.splitlines()
        grid = []
        utime = int(time.time())
        
        for line in lines:
            if "Product Valid At :" in line:
                try:
                    ts_str = line.split(":", 1)[1].strip().replace(" UTC", "")
                    utime = int(time.mktime(time.strptime(ts_str, "%Y-%m-%d %H:%M")))
                except: pass
            if line.startswith("#") or not line.strip() or "---" in line or "|" not in line:
                continue
            parts = line.split("|")
            vals = [float(v) for v in parts[1].split()]
            grid.append(vals) 

        if not grid: return False

        # Stats
        flattened = [v for row in grid for v in row]
        dmax, dmin = max(flattened), min(flattened)
        dmean = sum(flattened) / len(flattened)
        
        with open(STATS_FILE, "a") as f:
            f.write(f"{utime} : {dmin:.2f} {dmax:.2f} {dmean:.2f}\n")
        
        # Map generation (660x330)
        # Interpolate the source grid (usually 90 longitudes x 37 latitudes)
        # We'll use PIL to interpolate then convert to 565
        rows = len(grid)
        cols = len(grid[0])
        img_src = Image.new("F", (cols, rows))
        for r in range(rows):
            for c in range(cols):
                img_src.putpixel((c, r), grid[r][c])
        
        img_interp = img_src.resize((660, 330), Image.Resampling.BILINEAR)
        
        # Write BMP 565 file
        w, h = 660, 330
        header = create_bmp_565_header(w, h)
        row_bytes = ((16 * w + 31) // 32) * 4
        pixel_data = bytearray(row_bytes * h)
        
        for y in range(h):
            for x in range(w):
                v = img_interp.getpixel((x, y))
                c565 = get_color_rgb565(v)
                struct.pack_into('<H', pixel_data, y * row_bytes + x * 2, c565)
                
        with open(MAP_FILE, "wb") as f:
            f.write(header)
            f.write(pixel_data)
            
        # Also save compressed version
        with open(MAP_FILE_Z, "wb") as f:
            f.write(zlib.compress(header + pixel_data))
            
        logger.info(f"Generated dynamic DRAP maps at {MAP_FILE} and {MAP_FILE_Z}")
        return True
    except Exception as e:
        logger.error(f"Error in DRAP service: {e}", exc_info=True)
        return False

def get_drap_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return f.read()
    return ""

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_and_process_drap()
