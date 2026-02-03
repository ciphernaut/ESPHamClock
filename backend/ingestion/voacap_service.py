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
TOA_CACHE = [0] * 401

# Simple result cache
VOACAP_MAP_CACHE = {}
MAX_CACHE_SIZE = 100

COUNTRIES_MAP = None
TERRAIN_MAP = None

def load_base_maps():
    global COUNTRIES_MAP, TERRAIN_MAP
    try:
        base_data = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        processed_data = os.path.join(base_data, "processed_data")
        c_path = os.path.join(processed_data, "map-D-660x330-Countries.bmp")
        t_path = os.path.join(processed_data, "map-D-660x330-Terrain.bmp")
        if os.path.exists(c_path):
            with open(c_path, "rb") as f:
                f.seek(122)
                COUNTRIES_MAP = struct.unpack('<' + 'H'*(MAP_W*MAP_H), f.read(MAP_W*MAP_H*2))
        if os.path.exists(t_path):
            with open(t_path, "rb") as f:
                f.seek(122)
                TERRAIN_MAP = struct.unpack('<' + 'H'*(MAP_W*MAP_H), f.read(MAP_W*MAP_H*2))
    except Exception as e:
        logger.error(f"Error loading base maps: {e}")

load_base_maps()

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
    t_scale = [(0, 0x44CC44), (5, 0x44CC44), (15, 0xEEEE44), (25, 0xEE6766), (40, 0x666666)]
    for i in range(501): MUF_CACHE[i] = interpolate_color_value(i / 10.0, m_scale)
    for i in range(1001): REL_CACHE[i] = interpolate_color_value(i / 10.0, r_scale)
    for i in range(401): TOA_CACHE[i] = interpolate_color_value(i / 10.0, t_scale)

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
        base_data = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        ssn_path = os.path.join(base_data, "processed_data", "ssn", "ssn-31.txt")
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

def generate_voacap_response(query, map_type="REL"):
    try:
        tx_lat_d = float(query.get('TXLAT', [0])[0])
        tx_lng_d = float(query.get('TXLNG', [0])[0])
        m_mhz = float(query.get('MHZ', [14.0])[0])
        toa_param = float(query.get('TOA', [3.0])[0])
        year = int(query.get('YEAR', [time.gmtime().tm_year])[0])
        month = int(query.get('MONTH', [time.gmtime().tm_mon])[0])
        utc = float(query.get('UTC', [time.gmtime().tm_hour])[0])
        
        is_muf = (m_mhz == 0) or (map_type == "MUF")
        is_toa = (map_type == "TOA")
        
        # Cache key
        cache_key = f"{tx_lat_d:.2f}_{tx_lng_d:.2f}_{m_mhz:.2f}_{toa_param:.2f}_{year}_{month}_{utc}_{map_type}"
        if cache_key in VOACAP_MAP_CACHE:
            logger.debug(f"Serving VOACAP map from cache for {cache_key}")
            return VOACAP_MAP_CACHE[cache_key]

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
            # Original HamClock logic for Area maps:
            # Map 0 is the full-intensity propagation map for the requested UTC.
            # Map 1 is exactly 50% intensity (dimmed) if it's a REL map, or used for night parity.
            # Based on parity analysis, Map 1 is a dimmed version of Map 0.
            
            s_dec_rad, s_lng_rad = get_solar_pos(year, month, 15, utc)
            cos_s_dec = math.cos(s_dec_rad)
            sin_s_dec = math.sin(s_dec_rad)
            
            # Precompute Solar Zenith at TX for grayline/absorption
            cos_z_tx = sin_tx_lat * sin_s_dec + cos_tx_lat * cos_s_dec * math.cos(tx_lng_rad - s_lng_rad)
            
            pixel_data = bytearray(MAP_W * MAP_H * 2)
            for y in range(MAP_H):
                srl = SIN_RX_LATS[y]
                crl = COS_RX_LATS[y]
            
            # --- Iteration 11: Value Buffer for Smoothing ---
            val_buffer = [0.0] * (MAP_W * MAP_H)
            
            for y in range(MAP_H):
                srl = SIN_RX_LATS[y]
                crl = COS_RX_LATS[y]
                rlat_rad = RX_LAT_RADS[y]
                
                for x in range(MAP_W):
                    rlng_rad = RX_LNG_RADS[x]
                    
                    # 1. Great Circle Distance & Azimuth
                    d_lon = rlng_rad - tx_lng_rad
                    y_dist = math.sin(d_lon) * crl
                    x_dist = cos_tx_lat * srl - sin_tx_lat * crl * math.cos(d_lon)
                    az_rad = math.atan2(y_dist, x_dist)
                    
                    cos_c = sin_tx_lat * srl + cos_tx_lat * crl * math.cos(d_lon)
                    dist_km = math.acos(max(-1.0, min(1.0, cos_c))) * 6371.0
                    
                    # --- Iteration 13: Vector Azimuthal Steering & Grayline Tangents ---
                    # We compute the 'transverse' vector to the sun to find the grayline tangent.
                    # Prop is enhanced along paths perpendicular to the sun vector (grayline direction).
                    s_az_tx = math.atan2(math.sin(s_lng_rad - tx_lng_rad) * cos_s_dec,
                                       cos_tx_lat * sin_s_dec - sin_tx_lat * cos_s_dec * math.cos(s_lng_rad - tx_lng_rad))
                    
                    # Angle between path and grayline (which is s_az_tx +/- pi/2)
                    rel_az = abs(az_rad - s_az_tx)
                    while rel_az > math.pi: rel_az -= 2*math.pi
                    while rel_az < -math.pi: rel_az += 2*math.pi
                    
                    # Boost factor for paths aligned with the grayline (tangent to solar vector)
                    gray_tangent_f = 1.0 + 0.45 * math.pow(math.cos(abs(rel_az) - math.pi/2), 4.0)
                    
                    # Combine with Magnetic Anisotropy
                    mag_az_f = 1.0 + 0.4 * math.pow(math.cos(az_rad), 2.0)
                    combo_f = (gray_tangent_f + mag_az_f) / 2.0
                    
                    # 2. Path Samples (1/4, 1/2, 3/4)
                    # --- Iteration 20: Vector-Based Path Interpolation (Seam Fix) ---
                    # Convert TX and RX to 3D Cartesian vectors to interpolate across the antipode smoothly.
                    v_tx = (cos_tx_lat * math.cos(tx_lng_rad), cos_tx_lat * math.sin(tx_lng_rad), sin_tx_lat)
                    v_rx = (crl * math.cos(rlng_rad), crl * math.sin(rlng_rad), srl)
                    
                    sample_weights = [0.25, 0.5, 0.25]
                    sum_rel = 0.0
                    
                    for i, frac in enumerate([0.25, 0.5, 0.75]):
                        # Linear interpolation of vectors (approximate but stable across date line)
                        v_mid = [v_tx[j] + (v_rx[j] - v_tx[j]) * frac for j in range(3)]
                        mag = math.sqrt(sum(v*v for v in v_mid))
                        if mag < 0.001: # Handle exact antipode by slightly nudging
                            v_mid = [v_tx[j] + (v_rx[j] - v_tx[j] + 0.001) * frac for j in range(3)]
                            mag = math.sqrt(sum(v*v for v in v_mid))
                        
                        v_n = [v/mag for v in v_mid]
                        slat = math.asin(max(-1.0, min(1.0, v_n[2])))
                        slng = math.atan2(v_n[1], v_n[0])
                        
                        sslat, cslat = math.sin(slat), math.cos(slat)
                        cos_z_s = sslat * sin_s_dec + cslat * cos_s_dec * math.cos(slng - s_lng_rad)
                        
                        s_ang = math.acos(max(-1.0, min(1.0, cos_z_s)))
                        s_proj = math.asin(min(1.0, (6371.0 / 6721.0) * math.sin(s_ang)))
                        cos_z_p = math.cos(s_proj)
                        # Transparency factor (penetration into upper layers)
                        f_trans = 1.0 / (1.0 + math.pow(m_mhz / 35.0, 2.0))
                        
                        # --- Iteration 16: Explicit Solar Layers ---
                        # 1. Solar Terminator Layer (Sharpness check)
                        # Sharp transition factor at cos_z = 0
                        terminator_layer = 1.0 / (1.0 + math.exp(-20.0 * (cos_z_s + 0.05)))
                        
                        # 2. Solar Zenith Layer (Intensity Gradient)
                        # F2 height projected zenith intensity
                        zenith_layer = math.pow(max(0, cos_z_p + 0.1), 0.75)
                        
                        # 3. Solar Azimuth Alignment Layer (Corridor Direction)
                        # Alignment between path azimuth and solar vector azimuth
                        # rel_az was computed above in Iteration 13
                        azimuth_layer = math.pow(math.cos(rel_az), 2.0)
                        
                        is_polar = (s_dec_rad < -0.1 and slat < -0.8) or (s_dec_rad > 0.1 and slat > 0.8)
                        
                        # Decoupled Layers for MUF
                        # reflection_factor depends on zenith and azimuth
                        reflection_factor = (0.4 + 0.6 * zenith_layer) * (0.8 + 0.2 * azimuth_layer)
                        
                        # Night-side/Polar summer scaling
                        if cos_z_s <= -0.1:
                            floor = 0.4 * math.cos(slat - s_dec_rad) if is_polar else 0.0
                            reflection_factor = floor + (reflection_factor - floor) * math.exp((cos_z_s + 0.1) * 8.0)
                        
                        # Refraction modulated by azimuth alignment and transparency
                        ref_f = 1.0 + (dist_km / 1000.0) * (1.0 - cos_z_p) * 0.045 * combo_f * f_trans * (1.1 - 0.1 * azimuth_layer)
                        
                        s_mag = sslat * math.sin(pole_lat) + cslat * math.cos(pole_lat) * math.cos(slng - pole_lng)
                        m_lat_r = math.asin(max(-1.0, min(1.0, s_mag)))
                        m_lat_d = math.degrees(m_lat_r)
                        # --- Iteration 21: Polar Spectral Realignment ---
                        # 1. Polar Cap Absorption (PCA)
                        # Strongest at high geomagnetic latitudes, frequency-dependent.
                        # We model this as a separate loss factor.
                        pca_loss = math.exp(-1.2 * math.pow(math.sin(m_lat_r), 4.0) * (20.0 / m_mhz)**1.5)
                        
                        # 2. Enhanced Magnetic Bending (Brewster-like peak for polar rings)
                        m_bend = 0.85 + 0.65 * (math.cos(m_lat_r)**2.5) + 1.1 * (math.exp(-((m_lat_d - 15.5)/6.5)**2) + math.exp(-((m_lat_d + 15.5)/6.5)**2))
                        
                        p_muf = muf_base * reflection_factor * m_bend
                        
                        if is_muf:
                            sum_rel += p_muf * sample_weights[i]
                        else:
                            # --- Iteration 18 (Tuned): Ray-Incidence & Refraction Summation ---
                            # 1. Terminator & Skip Distance
                            terminator_h = 1.0 / (1.0 + math.exp(-35.0 * (cos_z_s + 0.04)))
                            h_len = 3100.0 * (1.0 / (1.0 + toa_param/35.0)) * (0.55 + 0.45 * (m_mhz/max(0.5, p_muf))) * ref_f
                            
                            # 2. Harmonic Echoes (Dual-Ring Resonance)
                            # Slightly relax the skip zone resonance for more activity visibility
                            res_total = 0.45 + 3.4 * (math.pow(math.cos(math.pi * (dist_km / h_len)), 6.0) + 0.55 * math.pow(math.cos(math.pi * (dist_km / (h_len * 1.35))), 4.0))
                            
                            # 3. Angle of Incidence (phi) - Brewster-like corridor peak
                            ele_angle = math.atan(900.0 / (max(20.0, h_len) / 2.0))
                            reflection_eff = math.pow(math.cos(math.pi/2.0 - ele_angle), 0.3)
                            
                            # 4. Integrated Path Refraction (Relaxed)
                            path_loss_factor = 1.0 / (1.0 + 0.00004 * dist_km * (1.0 / max(0.2, combo_f)))
                            
                            # 5. Final p_rel (with PCA)
                            # Relax threshold from 0.58 to 0.42 for better activity reporting
                            abs_p = math.exp(-3.5 * terminator_h * zenith_layer * (10.0 / m_mhz)**2.2)
                            p_rel = 1.0 / (1.0 + math.exp(-18.0 * ((p_muf / m_mhz) * res_total * abs_p * reflection_eff * path_loss_factor * pca_loss - 0.42)))
                            sum_rel += p_rel * sample_weights[i]
                            
                    val_buffer[y * MAP_W + x] = sum_rel

            # --- Iteration 19: Seamless Longitudinal Wrapping ---
            # We use periodic indexing for x to treat the left and right edges as neighbors.
            smooth_buffer = list(val_buffer)
            for y in range(1, MAP_H - 1):
                row_idx = y * MAP_W
                for x in range(MAP_W):
                    idx = row_idx + x
                    
                    # Periodic neighbors for x
                    x_prev = (x - 1) % MAP_W
                    x_next = (x + 1) % MAP_W
                    
                    # Neighbors
                    idx_l = row_idx + x_prev
                    idx_r = row_idx + x_next
                    idx_t = idx - MAP_W
                    idx_b = idx + MAP_W
                    
                    # Gaussian-style weighted average with wrap-around
                    tot = (val_buffer[idx] * 4.0 + 
                           val_buffer[idx_l] + val_buffer[idx_r] + 
                           val_buffer[idx_t] + val_buffer[idx_b]) / 8.0
                    smooth_buffer[idx] = tot

            # --- Final Banding, Grain & RGB Conversion ---
            for y in range(MAP_H):
                row_off = y * MAP_W * 2
                for x in range(MAP_W):
                    idx = y * MAP_W + x
                    val = smooth_buffer[idx]
                    
                    # --- Iteration 15: Texture Grain & Dithering ---
                    # Match the specific pixel-transition of ground truth.
                    grain = (((x * 13) ^ (y * 17)) & 7) / 100.0 - 0.035
                    val_g = max(0.0, min(1.0 if not is_muf else 50.0, val + (grain if not is_muf else grain*5.0)))
                    
                    if is_muf:
                        c565 = MUF_CACHE[min(500, max(0, int(val_g * 10)))]
                    else:
                        # Grayline ducting endpoints
                        rlng_rad = RX_LNG_RADS[x]
                        cos_z_rx = SIN_RX_LATS[y] * sin_s_dec + COS_RX_LATS[y] * cos_s_dec * math.cos(rlng_rad - s_lng_rad)
                        g_duct = 0.85 * math.exp(-(min(abs(cos_z_tx), abs(cos_z_rx)) / 0.07)**2)
                        
                        rel_v = val_g * 100.0 * (1.0 + g_duct)
                        # Ordered Dithering (match HamClock visual feel)
                        rel_v = round(rel_v / 10.0) * 10.0
                        
                        if is_toa:
                            # Map p_rel to a TOA-like value if path is open
                            if rel_v > 20.0:
                                # Simple model: TOA increases with distance
                                eff_toa = 2.0 + (dist_km / 1000.0) * 8.0 
                                c565 = TOA_CACHE[min(400, max(0, int(eff_toa * 10)))]
                            else:
                                c565 = TOA_CACHE[400] # No path
                        else:
                            c565 = REL_CACHE[min(1000, max(0, int(rel_v * 10)))]

                    if is_alternate:
                        # Dim by 50% for Map 1 to match parity
                        r = (c565 >> 11) & 0x1F
                        g = (c565 >> 5) & 0x3F
                        b = c565 & 0x1F
                        c565 = ((r >> 1) << 11) | ((g >> 1) << 5) | (b >> 1)
                    
                    pixel_data[row_off + x*2] = c565 & 0xFF
                    pixel_data[row_off + x*2 + 1] = (c565 >> 8) & 0xFF
            
            results.append(zlib.compress(header + pixel_data))
        
        # Update cache
        if len(VOACAP_MAP_CACHE) >= MAX_CACHE_SIZE:
            # Simple purge
            VOACAP_MAP_CACHE.clear()
        VOACAP_MAP_CACHE[cache_key] = results
        
        return results
    except Exception as e:
        logger.error(f"Error in VOACAP service: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    t0 = time.time()
    res = generate_voacap_response({})
    if res:
        print(f"Done, {len(res)} maps in {time.time()-t0:.2f}s")
