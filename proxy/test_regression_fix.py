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

if __name__ == "__main__":
    try:
        test_weather_variance()
        test_solar_variance()
        test_coeff_variance()
        print("\nAll regression tests passed!")
    except AssertionError as e:
        print(f"\nTest failed!")
        sys.exit(1)
