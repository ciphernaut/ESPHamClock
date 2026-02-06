import sys
import requests
import difflib
import re

def clean_response(text, endpoint):
    """
    Remove dynamic 'noise' from response based on endpoint type.
    """
    if "spacewx" in endpoint or "get_de.txt" in endpoint:
        # Remove timestamps, usually at the end of lines or specific fields
        # This is a placeholder for actual semantic cleaning logic
        lines = text.splitlines()
        cleaned = []
        for line in lines:
            # Example: Remove 'at 12:34:56' patterns
            line = re.sub(r'at \d{1,2}:\d{2}:\d{2}', 'at [TIME]', line)
            cleaned.append(line)
        return "\n".join(cleaned)
    
    return text

def compare(url1, url2, endpoint):
    try:
        print(f"  [DEBUG] Fetching R1: {url1}")
        r1 = requests.get(url1, timeout=5)
        print(f"  [DEBUG] Fetching R2: {url2}")
        r2 = requests.get(url2, timeout=5)
        
        if r1.status_code != r2.status_code:
            print(f"FAILED: Status Code Mismatch ({r1.status_code} vs {r2.status_code})")
            return False
            
        t1 = clean_response(r1.text, endpoint)
        t2 = clean_response(r2.text, endpoint)
        
        if t1 == t2:
            print("OK: Parity Achieved (Semantic)")
            return True
        else:
            print("FAIL: Discrepancy Found")
            diff = difflib.unified_diff(
                t1.splitlines(), t2.splitlines(),
                fromfile='ax4test', tofile='ax4upstream'
            )
            for line in diff:
                print(line)
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: compare_endpoint.py <url1> <url2> <endpoint_name>")
        sys.exit(1)
        
    url1 = sys.argv[1]
    url2 = sys.argv[2]
    endpoint = sys.argv[3]
    
    success = compare(url1, url2, endpoint)
    sys.exit(0 if success else 1)
