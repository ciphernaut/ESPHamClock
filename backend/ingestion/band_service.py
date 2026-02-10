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
    
    bands = [3.5, 5.3, 7.0, 10.1, 14.0, 18.1, 21.0, 24.9, 28.0]
    
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
    Use the refined VOACAP-based model for consistency.
    """
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    
    # voacap_service.calculate_point_propagation returns (muf, rel)
    _, rel = voacap_service.calculate_point_propagation(tlat, tlng, rlat, rlng, mhz, toa, year, month, float(utc), ssn)
    return rel

if __name__ == "__main__":
    test_query = {'TXLAT': ['45'], 'TXLNG': ['-75'], 'RXLAT': ['51'], 'RXLNG': ['0']}
    print(get_band_conditions(test_query))
