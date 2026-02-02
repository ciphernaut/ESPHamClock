import os
import time
import datetime
import logging
try:
    from ingestion import voacap_service
except ImportError:
    import voacap_service

logger = logging.getLogger(__name__)

def get_band_conditions(query):
    """
    Generate band conditions text in HamClock format.
    """
    tx_lat = float(query.get('TXLAT', [0])[0])
    tx_lng = float(query.get('TXLNG', [0])[0])
    rx_lat = float(query.get('RXLAT', [0])[0])
    rx_lng = float(query.get('RXLNG', [0])[0])
    
    # Map Numerical Mode to Names
    # 38 -> SSB, 19 -> FT8 (based on parity analysis)
    raw_mode = query.get('MODE', ['CW'])[0]
    mode_map = {
        '38': 'SSB',
        '39': 'USB',
        '40': 'LSB',
        '19': 'FT8',
        '1': 'CW'
    }
    mode_name = mode_map.get(raw_mode, raw_mode)
    
    # Map Power
    power = query.get('POW', query.get('POWER', ['100']))[0]
    power_str = f"{power}W"
    
    # Map Path (0 -> SP, 1 -> LP)
    raw_path = query.get('PATH', ['0'])[0]
    path_str = "LP" if raw_path == '1' else "SP"
    
    # TOA Header Formatting
    raw_toa = query.get('TOA', ['3'])[0]
    try:
        toa_val = float(raw_toa)
        # Format as integer if possible (3.0 -> 3)
        toa_hdr = str(int(toa_val)) if toa_val == int(toa_val) else f"{toa_val:.1f}"
    except:
        toa_hdr = raw_toa

    current_utc = int(query.get('UTC', [time.gmtime().tm_hour])[0])
    ssn = voacap_service.get_ssn()
    
    bands = [3.5, 7.0, 10.1, 14.0, 18.1, 21.0, 24.9, 28.0, 50.0]
    
    lines = []
    
    # Helper to get reliability for all bands at a specific UTC
    def get_rels_for_utc(utc_val):
        rels = []
        for mhz in bands:
            rel = calculate_point_reliability(tx_lat, tx_lng, rx_lat, rx_lng, mhz, float(raw_toa), utc_val, ssn)
            rels.append(f"{rel:.2f}")
        return ",".join(rels)

    # Line 1: Current condition
    lines.append(get_rels_for_utc(current_utc))
    
    # Line 2: Parameters - Match exactly: 50W,SSB,TOA>3,LP,S=97
    lines.append(f"{power_str},{mode_name},TOA>{toa_hdr},{path_str},S={int(ssn)}")
    
    # Lines 3-26: Hourly forecast (1 to 23, then 0)
    for h in range(1, 24):
        lines.append(f"{h} {get_rels_for_utc(h)}")
    lines.append(f"0 {get_rels_for_utc(0)}")
    
    return "\n".join(lines) + "\n"

def calculate_point_reliability(tlat, tlng, rlat, rlng, mhz, toa, utc, ssn):
    """
    Simplified point-to-point implementation of the VOACAP-like model in voacap_service.py
    """
    import math
    
    tlat_r, tlng_r = math.radians(tlat), math.radians(tlng)
    rlat_r, rlng_r = math.radians(rlat), math.radians(rlng)
    
    # Basic geometry
    cos_c = math.sin(tlat_r) * math.sin(rlat_r) + math.cos(tlat_r) * math.cos(rlat_r) * math.cos(rlng_r - tlng_r)
    dist_km = math.acos(max(-1.0, min(1.0, cos_c))) * 6371.0
    
    # MUF model (Simplified from voacap_service.py)
    # Solar position
    year = time.gmtime().tm_year
    month = time.gmtime().tm_mon
    
    def get_solar_pos(y, m, d, u):
        # Estimate day of year
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        doy = sum(days_in_month[:m-1]) + d
        dec = 23.44 * math.sin(math.radians(360.0/365.25 * (doy - 81)))
        sub_lng = (12.0 - u) * 15.0
        return math.radians(dec), math.radians(sub_lng)

    s_dec, s_lng = get_solar_pos(year, month, 15, utc)
    
    # Midpoint solar zenith
    v_tx = (math.cos(tlat_r) * math.cos(tlng_r), math.cos(tlat_r) * math.sin(tlng_r), math.sin(tlat_r))
    v_rx = (math.cos(rlat_r) * math.cos(rlng_r), math.cos(rlat_r) * math.sin(rlng_r), math.sin(rlat_r))
    v_mid = [(v_tx[i] + v_rx[i]) / 2.0 for i in range(3)]
    mag = math.sqrt(sum(v*v for v in v_mid))
    v_n = [v/(mag if mag > 0 else 0.001) for v in v_mid]
    
    slat_m = math.asin(max(-1.0, min(1.0, v_n[2])))
    slng_m = math.atan2(v_n[1], v_n[0])
    
    cos_z = math.sin(slat_m) * math.sin(s_dec) + math.cos(slat_m) * math.cos(s_dec) * math.cos(slng_m - s_lng)
    
    # MUF estimate
    muf_base = 5.0 + 0.1 * ssn
    zenith_f = math.pow(max(0, cos_z + 0.1), 0.75)
    reflection_f = 0.4 + 0.6 * zenith_f
    
    # Night floor
    if cos_z <= -0.1:
        reflection_f = 0.1 + (reflection_f - 0.1) * math.exp((cos_z + 0.1) * 8.0)
        
    p_muf = muf_base * reflection_f * 1.5 # Boost factor for MUF
    
    # REL model
    # Skip resonance
    h_len = 3100.0 * (1.0 / (1.0 + toa/35.0))
    res = 0.45 + 3.4 * (math.pow(math.cos(math.pi * (dist_km / h_len)), 6.0))
    
    # Absorption
    abs_p = math.exp(-3.5 * zenith_f * (10.0 / (mhz + 1.0))**2.2)
    
    # Path loss
    path_loss = 1.0 / (1.0 + 0.00004 * dist_km)
    
    p_rel = 1.0 / (1.0 + math.exp(-18.0 * ((p_muf / mhz) * res * abs_p * path_loss - 0.42)))
    
    return max(0.0, min(1.0, p_rel))

if __name__ == "__main__":
    test_query = {'TXLAT': ['45'], 'TXLNG': ['-75'], 'RXLAT': ['51'], 'RXLNG': ['0']}
    print(get_band_conditions(test_query))
