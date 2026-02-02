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
    Format:
    Current reliability (9 bands)
    Parameters summary
    H1 R80,R40,R30,R20,R17,R15,R12,R10,R6
    ...
    H0 R80,...
    """
    tx_lat = float(query.get('TXLAT', [0])[0])
    tx_lng = float(query.get('TXLNG', [0])[0])
    rx_lat = float(query.get('RXLAT', [0])[0])
    rx_lng = float(query.get('RXLNG', [0])[0])
    mode = query.get('MODE', ['CW'])[0]
    power = query.get('POWER', ['100W'])[0]
    toa = query.get('TOA', ['3'])[0]
    path = query.get('PATH', ['SP'])[0]
    
    current_utc = time.gmtime().tm_hour
    ssn = voacap_service.get_ssn()
    
    bands = [3.5, 7.0, 10.1, 14.0, 18.1, 21.0, 24.9, 28.0, 50.0]
    
    lines = []
    
    # Helper to get reliability for all bands at a specific UTC
    def get_rels_for_utc(utc_val):
        rels = []
        for mhz in bands:
            # We use a modified query for a single point reliability
            # voacap_service.generate_voacap_response is designed for maps,
            # but we can call it or extract its core logic.
            # For now, we'll implement a simple point-to-point reliability calculator
            # based on the same model in voacap_service or reuse it.
            
            # Since generate_voacap_response is quite integrated with map generation,
            # Let's see if we can extract a helper or just implement a simpler version here.
            # Reuse logic from voacap_service indirectly by calling it if possible?
            # No, generate_voacap_response returns a whole map.
            
            # I'll implement a point-to-point REL helper here or in voacap_service.
            rel = calculate_point_reliability(tx_lat, tx_lng, rx_lat, rx_lng, mhz, float(toa), utc_val, ssn)
            rels.append(f"{rel:.2f}")
        return ",".join(rels)

    # Line 1: Current condition
    lines.append(get_rels_for_utc(current_utc))
    
    # Line 2: Parameters
    lines.append(f"{power},{mode},TOA>{toa},{path},S={int(ssn)}")
    
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
