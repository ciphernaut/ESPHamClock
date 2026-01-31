import os
import math
import time
import struct
import zlib
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# Constants for map generation
MAP_W = 660
MAP_H = 330
DATA_DIR = "processed_data/voacap"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def create_bmp_565_header(w, h):
    core_size = 14
    dib_size = 108
    hdr_len = core_size + dib_size
    row_bytes = ((16 * w + 31) // 32) * 4
    pix_bytes = row_bytes * h
    file_bytes = hdr_len + pix_bytes
    
    header = bytearray(b'BM')
    header += struct.pack('<L', file_bytes)    # size
    header += struct.pack('<H', 0)
    header += struct.pack('<H', 0)
    header += struct.pack('<L', hdr_len)       # offset
    header += struct.pack('<L', dib_size)      # size
    header += struct.pack('<l', w)
    header += struct.pack('<l', -h)            # top-down
    header += struct.pack('<H', 1)
    header += struct.pack('<H', 16)
    header += struct.pack('<L', 3)             # BI_BITFIELDS
    header += struct.pack('<L', pix_bytes)
    header += struct.pack('<l', 0)
    header += struct.pack('<l', 0)
    header += struct.pack('<L', 0)
    header += struct.pack('<L', 0)
    header += struct.pack('<L', 0xF800)        # R
    header += struct.pack('<L', 0x07E0)        # G
    header += struct.pack('<L', 0x001F)        # B
    header += struct.pack('<L', 0x0000)        # A
    header += struct.pack('<L', 1)
    header += bytearray(36)
    header += struct.pack('<L', 0)
    header += struct.pack('<L', 0)
    header += struct.pack('<L', 0)
    return header

def get_ssn():
    """Tries to get current SSN from ssn-31.txt"""
    try:
        ssn_path = "processed_data/ssn/ssn-31.txt"
        if os.path.exists(ssn_path):
            with open(ssn_path, "r") as f:
                content = f.read().strip()
                # Assuming simple format: val date ...
                # or just the first number
                return float(content.split()[0])
    except: pass
    return 70.0 # Default

def get_rel_color_565(rel):
    """
    Map reliability (0-100) to RGB565.
    Scale from mapmanage.cpp: 
    0:0,0,0, 10:4E,13,8A, 25:00,1E,F5, 40:78,FB,D6, 60:78,FA,4D, 80:FE,FD,54, 95:EC,6F,2D, 100:E9,33,23
    """
    r, g, b = 0, 0, 0
    if rel <= 0: pass
    elif rel < 10: r,g,b = int(rel/10*0x4E), int(rel/10*0x13), int(rel/10*0x8A)
    elif rel < 25: r,g,b = 0, int((rel-10)/15*0x1E), int(0x8A + (rel-10)/15*(0xF5-0x8A))
    elif rel < 40: r,g,b = int((rel-25)/15*0x78), 0xFB, int(0xF5 + (rel-25)/15*(0xD6-0xF5))
    elif rel < 60: r,g,b = 0x78, int(0xFB + (rel-40)/20*(0xFA-0xFB)), int(0xD6 + (rel-40)/20*(0x4D-0xD6))
    elif rel < 80: r,g,b = int(0x78 + (rel-60)/20*(0xFE-0x78)), int(0xFA + (rel-60)/20*(0xFD-0xFA)), int(0x4D + (rel-60)/20*(0x54-0x4D))
    elif rel < 95: r,g,b = int(0xFE + (rel-80)/15*(0xEC-0xFE)), int(0xFD + (rel-80)/15*(0x6F-0xFD)), int(0x54 + (rel-80)/15*(0x2D-0x54))
    else: r,g,b = 0xE9, 0x33, 0x23
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def get_muf_color_565(muf):
    """
    Map MUF (0-50 MHz) to RGB565.
    Scale from mapmanage.cpp m_scale: 
    0:0,0,0, 4:4E,13,8A, 9:00,1E,F5, 15:78,FB,D6, 20:78,FA,4D, 27:FE,FD,54, 30:EC,6F,2D, 35:E9,33,23
    """
    r, g, b = 0, 0, 0
    if muf <= 0: pass
    elif muf < 4: r,g,b = int(muf/4*0x4E), int(muf/4*0x13), int(muf/4*0x8A)
    elif muf < 9: r,g,b = 0, int((muf-4)/5*0x1E), int(0x8A + (muf-4)/5*(0xF5-0x8A))
    # ... Simplified interpolation
    elif muf < 15: r,g,b = 0x78, 0xFB, 0xD6
    elif muf < 20: r,g,b = 0x78, 0xFA, 0x4D
    elif muf < 27: r,g,b = 0xFE, 0xFD, 0x54
    elif muf < 35: r,g,b = 0xE9, 0x33, 0x23
    else: r,g,b = 0xFF, 0xFF, 0xFF
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def calculate_muf(tx_lat, tx_lng, rx_lat, rx_lng, utc, ssn, is_night):
    """Very simplified MUF model"""
    # Base MUF depends on SSN
    base = 10 + 0.1 * ssn
    # Night factor
    if is_night: base *= 0.6
    # Distance factor (approximate)
    dist = math.sqrt((tx_lat-rx_lat)**2 + (tx_lng-rx_lng)**2)
    dist_factor = 1.0 + 0.5 * math.sin(min(math.pi, dist/40))
    return base * dist_factor

def generate_voacap_response(query):
    try:
        tx_lat = float(query.get('TXLAT', [0])[0])
        tx_lng = float(query.get('TXLNG', [0])[0])
        ssn = get_ssn()
        mhz = float(query.get('MHZ', [0])[0])
        is_muf = (mhz == 0)
        
        # Generate two maps: 'Day' and 'Night'
        # In this shim, 'Day' will assume sun is overhead at some point,
        # 'Night' will assume sun is on the other side.
        
        results = []
        for is_night_map in [False, True]:
            pixel_data = bytearray(MAP_W * MAP_H * 2)
            row_bytes = ((16 * MAP_W + 31) // 32) * 4 # row padding
            for y in range(MAP_H):
                rx_lat = 90 - (y * 180 / MAP_H)
                for x in range(MAP_W):
                    rx_lng = -180 + (x * 360 / MAP_W)
                    
                    val = calculate_muf(tx_lat, tx_lng, rx_lat, rx_lng, 0, ssn, is_night_map)
                    
                    if not is_muf:
                        # Reliability: scale 0-100 based on MHZ vs MUF
                        rel = 0
                        if val > mhz:
                            rel = min(100, (val - mhz) * 10 + 20)
                        elif val > mhz * 0.8:
                            rel = (val / mhz) * 20
                        c565 = get_rel_color_565(rel)
                    else:
                        c565 = get_muf_color_565(val)
                    
                    struct.pack_into('<H', pixel_data, y * row_bytes + x * 2, c565)
            
            header = create_bmp_565_header(MAP_W, MAP_H)
            results.append(zlib.compress(header + pixel_data))
            
        return results
    except Exception as e:
        logger.error(f"Error in VOACAP service: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = generate_voacap_response({'TXLAT': [45], 'TXLNG': [-90], 'MHZ': [0]})
    if res:
        print(f"Lengths: {len(res[0])} {len(res[1])}")
