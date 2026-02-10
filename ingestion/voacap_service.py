import os
import math
import time
import struct
import zlib
import logging

logger = logging.getLogger(__name__)

MAP_W = 660
MAP_H = 330

MUF_CACHE = [0] * 501
REL_CACHE = [0] * 1001

def interpolate_color_value(val, scale):
    if val <= scale[0][0]: c = scale[0][1]
    elif val >= scale[-1][0]: c = scale[-1][1]
    else:
        for i in range(len(scale) - 1):
            v1, c1 = scale[i]
            v2, c2 = scale[i+1]
            if v1 <= val <= v2:
                f = (val - v1) / (v2 - v1)
                r1, g1, b1 = (c1 >> 16) & 0xFF, (c1 >> 8) & 0xFF, c1 & 0xFF
                r2, g2, b2 = (c2 >> 16) & 0xFF, (c2 >> 8) & 0xFF, c2 & 0xFF
                r, g, b = int(r1+(r2-r1)*f), int(g1+(g2-g1)*f), int(b1+(b2-b1)*f)
                return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    r, g, b = (c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def precompute_scales():
    m_scale = [(0, 0), (4, 0x4E138A), (9, 0x001EF5), (15, 0x78FBD6), (20, 0x78FA4D), (27, 0xFEFD54), (30, 0xEC6F2D), (35, 0xE93323)]
    r_scale = [(0, 0x666666), (21, 0xEE6766), (40, 0xEEEE44), (60, 0xEEEE44), (83, 0x44CC44), (100, 0x44CC44)]
    for i in range(501): MUF_CACHE[i] = interpolate_color_value(i / 10.0, m_scale)
    for i in range(1001): REL_CACHE[i] = interpolate_color_value(i / 10.0, r_scale)

precompute_scales()

def create_bmp_565_header(w, h):
    core_size = 14
    dib_size = 108
    hdr_len = core_size + dib_size
    row_bytes = (w * 2)
    pix_bytes = row_bytes * h
    file_bytes = hdr_len + pix_bytes
    
    # 14 bytes core
    header = bytearray(b'BM')
    header += struct.pack('<LHH L', file_bytes, 0, 0, hdr_len)
    
    # 108 bytes DIB (BITMAPV4HEADER)
    # 26 L/l/H items = 26 items total
    header += struct.pack('<LllHHLLllLLLLLLLLLLLLLL',
        dib_size, w, -h, 1, 16, 3, pix_bytes, 0, 0, 0, 0,
        0xF800, 0x07E0, 0x001F, 0x0000, 1,
        0, 0, 0, 0, 0, 0, 0, 0, 0 
    )
    return header

def get_ssn():
    return 70.0

def generate_voacap_response(query):
    tx_lat_d = float(query.get('TXLAT', [0])[0])
    tx_lng_d = float(query.get('TXLNG', [0])[0])
    mhz = float(query.get('MHZ', [0])[0])
    is_muf = (mhz == 0)
    
    results = []
    header = create_bmp_565_header(MAP_W, MAP_H)
    
    for is_night in [False, True]:
        pixel_data = bytearray(MAP_W * MAP_H * 2)
        for y in range(MAP_H):
            rx_lat = 90 - (y * 180 / MAP_H)
            for x in range(MAP_W):
                rx_lng = -180 + (x * 360 / MAP_W)
                
                # Distance and time variation
                d_lat = rx_lat - tx_lat_d
                d_lng = (rx_lng - tx_lng_d + 180) % 360 - 180
                dist = math.sqrt(d_lat*d_lat + d_lng*d_lng)
                
                # Diurnal variation based on x (longitude)
                val = 15 + 10 * math.cos(math.radians(rx_lng + (180 if is_night else 0)))
                val += 5 * math.cos(math.radians(rx_lat * 2))
                # TX sensitivity: slightly boost MUF near TX
                val += 10 * math.exp(-dist/25.0)
                
                if is_muf:
                    c565 = MUF_CACHE[min(500, max(0, int(val * 10)))]
                else:
                    rel = min(100, max(0, (val - mhz + 10) * 5))
                    c565 = REL_CACHE[int(rel * 10)]
                
                offset = (y * MAP_W + x) * 2
                pixel_data[offset] = c565 & 0xFF
                pixel_data[offset+1] = (c565 >> 8) & 0xFF
        
        results.append(zlib.compress(header + pixel_data))
    return results

if __name__ == "__main__":
    res = generate_voacap_response({'TXLAT': [45], 'TXLNG': [-90], 'MHZ': [0]})
    print(f"Done, {len(res)} maps")
