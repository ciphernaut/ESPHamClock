import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parity_checker import TextFuzzyChecker, ParityResult

def test_weather_variance():
    print("Testing Weather Variance (TextFuzzyChecker)...")
    checker = TextFuzzyChecker()
    
    # Matching headers/city/attribution but slightly different numbers
    orig = b"city=Blackwater\ntemperature_c=23.56\nhumidity_percent=80\nattribution=openweathermap.org\nconditions=Rain"
    local = b"city=Rolleston\ntemperature_c=24.00\nhumidity_percent=82\nattribution=wttr.in\nconditions=rain" # normalized case
    
    res = checker.compare("wx.pl", orig, local)
    print(f"  Weather Case: {res.status} (Expected: Drift) - {res.message}")
    assert res.status == ParityResult.DRIFT

def test_solar_variance():
    print("\nTesting Solar/Bz Variance...")
    checker = TextFuzzyChecker()
    
    # Bz.txt sample: UNIX TIMESTAMP + Values
    orig = b"# UNIX Bx By Bz Bt\n1769950560   -1.4   -3.3   -3.6    5.0"
    local = b"# UNIX Bx By Bz Bt\n1769950561   -1.5   -3.2   -3.7    5.1"
    
    res = checker.compare("Bz.txt", orig, local)
    print(f"  Solar Case: {res.status} (Expected: Drift) - {res.message}")
    assert res.status == ParityResult.DRIFT

def test_coeff_variance():
    print("\nTesting Coefficient Variance...")
    checker = TextFuzzyChecker()
    
    # rank2_coeffs.txt sample
    orig = b"0       0        0.05    -6              // Sunspot_N"
    local = b"0       0        0.06    -6              // Sunspot_N"
    
    res = checker.compare("rank2_coeffs.txt", orig, local)
    print(f"  Coeff Case: {res.status} (Expected: Drift) - {res.message}")
    assert res.status == ParityResult.DRIFT

def test_noaaswx_parity():
    print("\nTesting NOAASpaceWX/noaaswx.txt Parity...")
    checker = get_checker("noaaswx.txt", [])
    
    # Authentic format: Letter  Val0 Val1 Val2 Val3
    orig = b"R  0 0 0 0\nS  0 0 0 0\nG  0 0 0 1\n"
    local = b"R  0 0 0 0\nS  0 0 0 0\nG  0 0 0 1\n"
    
    res = checker.compare("noaaswx.txt", orig, local)
    print(f"  noaaswx Case: {res.status} (Expected: Match)")
    assert res.status == ParityResult.MATCH

def test_rank2_coeffs_parity():
    print("\nTesting NOAASpaceWX/rank2_coeffs.txt Parity...")
    checker = get_checker("rank2_coeffs.txt", [])
    
    # First few lines of authentic file
    orig = b"# y = ax^2 + bx + c, where x = raw space weather value, y = small integer for ranking roughly -10..5\n0       0        0.05    -6              // Sunspot_N      60 => -3       200 => 4\n"
    local = b"# y = ax^2 + bx + c, where x = raw space weather value, y = small integer for ranking roughly -10..5\n0       0        0.05    -6              // Sunspot_N      60 => -3       200 => 4\n"
    
    res = checker.compare("rank2_coeffs.txt", orig, local)
    print(f"  rank2_coeffs Case: {res.status} (Expected: Match)")
    assert res.status == ParityResult.MATCH

if __name__ == "__main__":
    from parity_checker import get_checker # Import inside __main__ to be available
    try:
        test_weather_variance()
        test_solar_variance()
        test_coeff_variance()
        test_noaaswx_parity()
        test_rank2_coeffs_parity()
        print("\nAll regression tests passed!")
    except AssertionError as e:
        print(f"\nTest failed!")
        sys.exit(1)
