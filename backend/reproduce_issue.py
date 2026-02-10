import sys
import os

# Add ingestion directory to path so we can import band_service
sys.path.append(os.path.join(os.path.dirname(__file__), 'ingestion'))

try:
    from ingestion import band_service
except ImportError:
    # Try direct import if running from backend dir
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from ingestion import band_service

def test_mode_mapping():
    test_cases = [
        ('19', 'CW'),
        ('13', 'FT8'),
        ('38', 'SSB'),
        ('17', 'FT4'),
        ('22', 'RTTY'),
        ('49', 'AM'),
        ('3', 'WSPR')
    ]

    print("Checking Mode Mappings...")
    all_passed = True
    for mode_val, expected_name in test_cases:
        query = {
            'TXLAT': ['0'], 'TXLNG': ['0'], 
            'RXLAT': ['0'], 'RXLNG': ['0'],
            'MODE': [mode_val],
            'UTC': ['12']
        }
        
        # We only care about the second line which contains the mode name
        result = band_service.get_band_conditions(query)
        lines = result.strip().split('\n')
        if len(lines) < 2:
            print(f"Error: Output too short for mode {mode_val}")
            all_passed = False
            continue
            
        # Line 2 format: 100W,SSB,TOA>3,LP,S=...
        params = lines[1].split(',')
        if len(params) < 2:
             print(f"Error: Malformed param line for mode {mode_val}: {lines[1]}")
             all_passed = False
             continue
             
        actual_name = params[1]
        
        if actual_name == expected_name:
            print(f"[PASS] Mode {mode_val} -> {actual_name}")
        else:
            print(f"[FAIL] Mode {mode_val} -> Expected {expected_name}, Got {actual_name}")
            all_passed = False

    if all_passed:
        print("\nAll Good!")
        exit(0)
    else:
        print("\nFailures Detected.")
        exit(1)

if __name__ == "__main__":
    test_mode_mapping()
