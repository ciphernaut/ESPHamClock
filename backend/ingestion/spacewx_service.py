
import os
import time
import logging
import math
from ingestion import voacap_service

logger = logging.getLogger(__name__)

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed_data")

class SpaceWxService:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_update = 0

    def get_latest_value(self, filepath, line_index=-1, value_index=0, is_date_prefixed=False):
        """Helper to read latest value from a data file"""
        try:
            full_path = os.path.join(DATA_DIR, filepath)
            if not os.path.exists(full_path):
                return "0"
            
            with open(full_path, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
                
            if not lines:
                return "0"
                
            line = lines[line_index]
            parts = line.split()
            
            if is_date_prefixed:
                # E.g. "2024 01 01 123" -> value is at index 3 (0-based) if 3 parts date
                # Actually our format is "YYYY MM DD Value" usually
                # ssn-31.txt: "2025 02 02 119"
                return parts[-1]
            else:
                return parts[value_index]
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return "0"

    def format_xray(self, flux_str):
        try:
            flux = float(flux_str)
        except:
            return "A0.0"
            
        if flux < 1e-7: return f"A{flux*1e8:.1f}"
        if flux < 1e-6: return f"B{flux*1e7:.1f}"
        if flux < 1e-5: return f"C{flux*1e6:.1f}"
        if flux < 1e-4: return f"M{flux*1e5:.1f}"
        return f"X{flux*1e4:.1f}"

    def get_spacewx_data(self, query, server_de_lat, server_de_lng, server_dx_lat, server_dx_lng):
        """
        Generate the content for get_spacewx.txt
        Format: key=value pairs, one per line.
        """
        # Check cache (primitive for now, better to cache full response content)
        # But DEDX depends on location, so we cache the *components* or key data only?
        # Actually, if query params change, response changes. cache key = query params + server state.
        
        # 1. Fetch Core Data
        ssn = self.get_latest_value("ssn/ssn-31.txt", is_date_prefixed=True)
        flux = self.get_latest_value("solar-flux/solarflux-99.txt")
        kp = self.get_latest_value("geomag/kindex.txt")
        swind = self.get_latest_value("solar-wind/swind-24hr.txt", value_index=1) # 1=Density match legacy magnitude
        
        # XRAY
        # Use last column (Long channel) for classification
        raw_xray = self.get_latest_value("xray/xray.txt", value_index=-1)
        xray = self.format_xray(raw_xray)
        
        # DRAP
        # drap/stats.txt format: timestamp : min max mean ...
        # parts: [ts, :, min, max, mean] -> max is index 3
        drap = self.get_latest_value("drap/stats.txt", value_index=3)
        
        # ... (rest of data fetching) ...
        
        # 2. Calculate DEDX
        # Determine locations
        try:
            lat_str = query.get('lat', [None])[0]
            lng_str = query.get('lng', [None])[0]
            
            de_lat = float(lat_str) if lat_str is not None else server_de_lat
            de_lng = float(lng_str) if lng_str is not None else server_de_lng
            
            dx_lat = server_dx_lat # Query usually only sends DE? Or does it send DX too?
            dx_lng = server_dx_lng
            # If client sends distinct DX in query, use it.
            # Legacy `get_spacewx.txt` usage in client: `httpHCGET (client, backend_host, "/get_spacewx.txt")`
            # It does NOT appear to send params in `webserver.cpp` or `spacewx.cpp`.
            # So we rely on SERVER STATE.
            
        except ValueError:
            de_lat, de_lng = server_de_lat, server_de_lng

        dedx = self.calculate_dedx(de_lat, de_lng, dx_lat, dx_lng, ssn)
        
        # 3. Format Response
        # Format matching legacy `spacewx.cpp` expectation
        lines = []
        lines.append(f"SSN={ssn}")
        lines.append(f"FLUX={flux}")
        lines.append(f"KP={kp}")
        lines.append(f"SOLWIND={swind}") 
        lines.append(f"XRAY={xray}")
        lines.append(f"DRAP={drap}") 
        # ... add others ...
        
        # DEDX is special: DEDX_band=reliability
        for band, rel in dedx.items():
            lines.append(f"DEDX_{band}={rel}")
            
        return "\n".join(lines)

    def calculate_dedx(self, de_lat, de_lng, dx_lat, dx_lng, ssn):
        """Calculate reliability for bands 80,40,30,20,17,15,12,10"""
        return voacap_service.calculate_dedx_for_bands(de_lat, de_lng, dx_lat, dx_lng, ssn)

# Singleton
spacewx_service = SpaceWxService()
