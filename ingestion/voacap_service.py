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
    header = bytearray(b'BM')
    header += struct.pack('<LHH L', file_bytes, 0, 0, hdr_len)
    header += struct.pack('<LllHHLLllLLLLLLLLLLLLLLLLLLL',
        dib_size, w, -h, 1, 16, 3, pix_bytes, 3780, 3780, 0, 0,
        0xF800, 0x07E0, 0x001F, 0x0000, 1,
        0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0
    )
    return header

def get_ssn():
    try:
        ssn_path = "processed_data/ssn/ssn-31.txt"
        if os.path.exists(ssn_path):
            with open(ssn_path, "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                if lines:
                    last_line = lines[-1]
                    parts = last_line.split()
                    if len(parts) >= 4:
                        return float(parts[3])
    except: pass
    return 70.0

# Precompute RX information
RX_LAT_VALS = [90.0 - (y * 180.0 / MAP_H) for y in range(MAP_H)]
RX_LNG_VALS = [-180.0 + (x * 360.0 / MAP_W) for x in range(MAP_W)]
RX_LAT_RADS = [math.radians(lat) for lat in RX_LAT_VALS]
RX_LNG_RADS = [math.radians(lng) for lng in RX_LNG_VALS]
COS_RX_LATS = [math.cos(r) for r in RX_LAT_RADS]
SIN_RX_LATS = [math.sin(r) for r in RX_LAT_RADS]

def get_solar_pos(year, month, day, utc):
    # Estimate day of year
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    doy = sum(days_in_month[:month-1]) + day
    # Solar declination
    dec = 23.44 * math.sin(math.radians(360.0/365.25 * (doy - 81)))
    # Sub-solar longitude (UTC 12:00 is roughly at 0 deg longitude at equinox)
    # Equation of time is ignored for this level of detail
    sub_lng = (12.0 - utc) * 15.0
    return math.radians(dec), math.radians(sub_lng)

def generate_voacap_response(query):
    try:
        tx_lat_d = float(query.get('TXLAT', [0])[0])
        tx_lng_d = float(query.get('TXLNG', [0])[0])
        m_mhz = float(query.get('MHZ', [14.0])[0])
        year = int(query.get('YEAR', [time.gmtime().tm_year])[0])
        month = int(query.get('MONTH', [time.gmtime().tm_mon])[0])
        utc = float(query.get('UTC', [time.gmtime().tm_hour])[0])
        
        is_muf = (m_mhz == 0)
        ssn = get_ssn()
        
        tx_lat_rad = math.radians(tx_lat_d)
        tx_lng_rad = math.radians(tx_lng_d)
        cos_tx_lat = math.cos(tx_lat_rad)
        sin_tx_lat = math.sin(tx_lat_rad)
        
        # Solar position for normalization
        # Note: HamClock protocol often sends multiple maps for day/night parity
        # but here we generate the specific snapshot for the requested UTC.
        
        results = []
        header = create_bmp_565_header(MAP_W, MAP_H)
        
        # North Magnetic Pole for Geomag Lat
        pole_lat = math.radians(80.5)
        pole_lng = math.radians(-72.5)
        
        # Model constants
        muf_base = 5.0 + 0.1 * ssn
        
        # We generate two maps: typically 'Day-like' and 'Night-like' as parity files,
        # but the actual logic should depend on the requested context.
        # Original server often returns two chunks.
        
        for is_alternate in [False, True]:
            # Alternate map is often a offset UTC or just a secondary view
            effective_utc = (utc + 12) % 24 if is_alternate else utc
            s_dec_rad, s_lng_rad = get_solar_pos(year, month, 15, effective_utc)
            cos_s_dec = math.cos(s_dec_rad)
            sin_s_dec = math.sin(s_dec_rad)
            
            pixel_data = bytearray(MAP_W * MAP_H * 2)
            for y in range(MAP_H):
                srl = SIN_RX_LATS[y]
                crl = COS_RX_LATS[y]
                row_offset = y * MAP_W * 2
                
                # Precompute Geomag Lat for the row
                # (Approximate: use lng in loop)
                
                for x in range(MAP_W): # wait, use MAP_W
                    pass
            
            # Re-implementing with full loop optimization
            for y in range(MAP_H):
                srl = SIN_RX_LATS[y]
                crl = COS_RX_LATS[y]
                row_offset = y * MAP_W * 2
                rlng_rads_y = RX_LNG_RADS
                
                for x in range(MAP_W):
                    rlng_rad = rlng_rads_y[x]
                    
                    # 1. Solar Zenith Angle (cos_z)
                    cos_z = srl * sin_s_dec + crl * cos_s_dec * math.cos(rlng_rad - s_lng_rad)
                    sza_deg = math.degrees(math.acos(max(-1.0, min(1.0, cos_z))))
                    # Smoothe sun factor with a sharper day-side preference
                    sun_factor = 0.45 + 0.55 * math.pow(max(0, cos_z + 0.1), 0.6)
                    if sza_deg > 95: sun_factor *= 0.6 # Night attenuation
                    
                    # 2. Geomagnetic Latitude
                    sin_mag = srl * math.sin(pole_lat) + crl * math.cos(pole_lat) * math.cos(rlng_rad - pole_lng)
                    mag_lat_rad = math.asin(max(-1.0, min(1.0, sin_mag)))
                    mag_lat_factor = 1.0 + 0.45 * (math.cos(mag_lat_rad) ** 2)
                    
                    # 3. Distance & Path Angle Modeling (Single + Multi-hop)
                    cos_c = sin_tx_lat * srl + cos_tx_lat * crl * math.cos(rlng_rad - tx_lng_rad)
                    dist_rad = math.acos(max(-1.0, min(1.0, cos_c)))
                    dist_km = dist_rad * 6371.0
                    
                    # Peak at F2 hop (~3100km) and secondary hop (~7500km)
                    m_factor = 1.1 + 1.9 * math.exp(-((dist_km - 3100)/1200)**2)
                    m_factor += 0.7 * math.exp(-((dist_km - 7500)/2500)**2)
                    
                    # 4. Terminator/Grayline Enhancement (Stronger, following corridors)
                    grayline = 0.45 * math.exp(-(cos_z / 0.12)**2)
                    
                    val = muf_base * sun_factor * mag_lat_factor * m_factor * (1.0 + grayline)
                    
                    if is_muf:
                        c565 = MUF_CACHE[min(500, max(0, int(val * 10)))]
                    else:
                        # Reliability scaling relative to target MHz
                        if val > m_mhz * 1.5: rel = 100
                        elif val > m_mhz: rel = 60 + (val / m_mhz - 1.0) * 80
                        elif val > m_mhz * 0.5: rel = (val / m_mhz - 0.5) * 120
                        else: rel = 0
                        c565 = REL_CACHE[min(1000, max(0, int(rel * 10)))]
                    
                    pixel_data[row_offset + x*2] = c565 & 0xFF
                    pixel_data[row_offset + x*2 + 1] = (c565 >> 8) & 0xFF
            
            results.append(zlib.compress(header + pixel_data))
        return results
    except Exception as e:
        logger.error(f"Error in VOACAP service: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    t0 = time.time()
    res = generate_voacap_response({'TXLAT': [45], 'TXLNG': [-90], 'MHZ': [0]})
    if res:
        print(f"Done, {len(res)} maps in {time.time()-t0:.2f}s")
