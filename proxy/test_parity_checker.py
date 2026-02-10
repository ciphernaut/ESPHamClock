import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parity_checker import get_checker, ParityResult

def test_text_fuzzy():
    print("Testing TextFuzzyChecker...")
    checker = get_checker("test.txt", [])
    
    orig = b"# extracted from CTY on Mon Feb 02\n1A 41.90 12.43 246"
    local = b"# extracted from CTY on Tue Feb 03\n1A 41.90 12.43 246"
    
    res = checker.compare("test.txt", orig, local)
    print(f"  Drift Case: {res.status} (Expected: Drift) - {res.message}")
    
    orig = b"Static line\nData: 100"
    local = b"Static line\nData: 200"
    res = checker.compare("test.txt", orig, local)
    print(f"  Diff Case: {res.status} (Expected: Diff) - {res.message}")

def test_json_semantic():
    print("\nTesting JsonChecker...")
    checker = get_checker("test.json", [])
    
    orig = b'{"a": 1, "b": 2}'
    local = b'{"b": 2, "a": 1}'
    res = checker.compare("test.json", orig, local)
    print(f"  Reorder Case: {res.status} (Expected: Match)")
    
    local = b'{"a": 1, "b": 3}'
    res = checker.compare("test.json", orig, local)
    print(f"  Value Diff Case: {res.status} (Expected: Diff)")

def test_image_structural():
    print("\nTesting ImageChecker...")
    checker = get_checker("test.bmp.z", [])
    
    # Fake SDO BMP.Z
    orig = b"SDO_HEADER_MAGIC" + b"A" * 1000
    local = b"SDO_HEADER_MAGIC" + b"B" * 1050 # within 20%
    res = checker.compare("test.bmp.z", orig, local)
    print(f"  SDO Variance Case: {res.status} (Expected: Drift) - {res.message}")
    
    local = b"SDO_HEADER_MAGIC" + b"B" * 2000 # outside 20%
    res = checker.compare("test.bmp.z", orig, local)
    print(f"  SDO Large Diff Case: {res.status} (Expected: Diff) - {res.message}")

if __name__ == "__main__":
    test_text_fuzzy()
    test_json_semantic()
    test_image_structural()
