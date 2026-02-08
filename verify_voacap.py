
import sys
import time

print("Starting verification...")
try:
    t0 = time.time()
    import backend.ingestion.voacap_service as voacap_service
    print(f"Imported voacap_service in {time.time()-t0:.2f}s")
    
    # Test the restored function specifically
    print("Testing calculate_point_propagation...")
    t0 = time.time()
    # Params: tx_lat, tx_lng, rx_lat, rx_lng, mhz, toa, year, month, utc, ssn, path=0
    muf, rel = voacap_service.calculate_point_propagation(0, 0, 10, 10, 14.0, 3.0, 2026, 2, 12, 100, path=0)
    print(f"Calculation result: MUF={muf:.2f}, REL={rel:.2f}")
    print(f"Calculation took {time.time()-t0:.4f}s")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
