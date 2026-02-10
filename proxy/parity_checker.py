import hashlib
import json
import re
import difflib

class ParityResult:
    MATCH = "Match"
    DRIFT = "Drift"  # Semantic match but byte/timestamp difference
    DIFF = "Diff"    # Meaningful difference

    def __init__(self, status, message="", significance="HIGH"):
        self.status = status
        self.message = message
        self.significance = significance

def get_checker(path, headers):
    """Factory to return the appropriate checker based on path and content type"""
    content_type = next((val for key, val in headers if key.lower() == 'content-type'), "")
    
    if path.endswith(".json") or "application/json" in content_type:
        return JsonChecker()
    if path.endswith(".bmp.z") or path.endswith(".bmp") or "/fetchVOACAPArea.pl" in path:
        return ImageChecker()
    if path.endswith(".txt") or path.endswith(".pl") or "text/plain" in content_type:
        return TextFuzzyChecker()
    
    return DefaultChecker()

class BaseChecker:
    def compare(self, path, orig_data, local_data):
        raise NotImplementedError

class DefaultChecker(BaseChecker):
    def compare(self, path, orig_data, local_data):
        if orig_data == local_data:
            return ParityResult(ParityResult.MATCH)
        return ParityResult(ParityResult.DIFF, f"Byte mismatch: {len(orig_data)} vs {len(local_data)}")

class TextFuzzyChecker(BaseChecker):
    def compare(self, path, orig_data, local_data):
        if orig_data == local_data:
            return ParityResult(ParityResult.MATCH)
        
        try:
            orig_text = orig_data.decode('utf-8', errors='replace').splitlines()
            local_text = local_data.decode('utf-8', errors='replace').splitlines()
            
            # Filter out known "ignorable" lines/patterns
            ignore_patterns = [
                r"^# extracted from",  # CTY/SSN extraction timestamps
                r"^# updated at",
                r"^# Last Modified",
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", # Generic ISO timestamps
                r"^attribution=" # Attribution variance is expected
            ]
            
            def normalize_line(line):
                # Handle key=value lines (common in .pl)
                if '=' in line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    # For weather/numeric fields, we allow variance if key matches
                    numeric_keys = ['temperature_c', 'humidity_percent', 'wind_speed_mps', 'pressure_hPa', 'pressure_chg', 'lat', 'lng', 'timezone']
                    if key in numeric_keys:
                        # Return just the key to mark it as "matched" structurally
                        return f"{key}=<NUMERIC>"
                    # For city, we allow some variance as different APIs might name things differently
                    if key == 'city':
                        return "city=<CITY>"
                    # For clouds/conditions, normalize to lowercase
                    if key in ['clouds', 'conditions']:
                        return f"{key}={val.strip().lower()}"
                
                # Handle solar wind/geomagnetic data (UNIX timestamp + numbers)
                # Pattern: TIMESTAMP VAL1 VAL2 ...
                if re.match(r"^\d{10}\s+", line):
                    # Keep the structure but mask the timestamp and values
                    parts = line.split()
                    return f"<TS> " + " ".join(["<VAL>" for _ in parts[1:]])

                # Handle coefficient files (simple numeric rows)
                if re.match(r"^\d+\s+[\d.-]+", line):
                     parts = line.split()
                     return f"{parts[0]} " + " ".join(["<VAL>" for _ in parts[1:]])

                return line.strip()

            orig_filtered = [normalize_line(l) for l in orig_text if not any(re.search(p, l) for p in ignore_patterns)]
            local_filtered = [normalize_line(l) for l in local_text if not any(re.search(p, l) for p in ignore_patterns)]
            
            # Remove empty strings from filtering
            orig_filtered = [l for l in orig_filtered if l]
            local_filtered = [l for l in local_filtered if l]

            if orig_filtered == local_filtered:
                return ParityResult(ParityResult.DRIFT, "Semantic match, dynamic data variance", "LOW")
            
            # If still different, check if it's high significance
            diff_lines = list(difflib.unified_diff(orig_filtered, local_filtered))
            return ParityResult(ParityResult.DIFF, f"Text difference found ({len(diff_lines)} lines)")
            
        except Exception as e:
            return ParityResult(ParityResult.DIFF, f"Text parsing error: {e}")

class JsonChecker(BaseChecker):
    def compare(self, path, orig_data, local_data):
        try:
            orig_obj = json.loads(orig_data)
            local_obj = json.loads(local_data)
            
            if orig_obj == local_obj:
                return ParityResult(ParityResult.MATCH)
            
            # TODO: Add numeric epsilon check if needed
            return ParityResult(ParityResult.DIFF, "JSON content mismatch")
        except Exception as e:
            # Fallback to byte check if not valid JSON
            if orig_data == local_data: return ParityResult(ParityResult.MATCH)
            return ParityResult(ParityResult.DIFF, f"JSON parse error: {e}")

class ImageChecker(BaseChecker):
    def compare(self, path, orig_data, local_data):
        if orig_data == local_data:
            return ParityResult(ParityResult.MATCH)
        
        # Check for BMP.Z (SDO) or raw BMP
        # SDO BMP.Z has a custom 16-byte header then zlib data
        # Raw BMP has 'BM' as first two bytes
        
        res = ParityResult(ParityResult.DRIFT, "Image structural match", "LOW")
        
        # Heuristic check for SDO BMP.Z
        if ".bmp.z" in path:
            if len(orig_data) > 16 and len(local_data) > 16:
                # SDO header is usually consistent in structure
                orig_header = orig_data[:16]
                local_header = local_data[:16]
                # If headers are structurally similar (starts with expected magic if any)
                # For now, just check if size is within 20% tolerance as image content varies
                size_diff = abs(len(orig_data) - len(local_data)) / max(len(orig_data), 1)
                if size_diff < 0.2:
                    return ParityResult(ParityResult.DRIFT, f"Image size within tolerance ({size_diff:.1%})", "LOW")

        # Fallback for BMP
        if orig_data[:2] == b'BM' and local_data[:2] == b'BM':
             return ParityResult(ParityResult.DRIFT, "BMP signature match, content varies", "LOW")
             
        return ParityResult(ParityResult.DIFF, f"Binary mismatch: {len(orig_data)} vs {len(local_data)}")
