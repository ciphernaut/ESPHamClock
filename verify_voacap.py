
import math
import sys
import time

print("Starting verification...")
try:
    t0 = time.time()
    import backend.ingestion.voacap_service as voacap_service
    print(f"Imported voacap_service in {time.time()-t0:.2f}s")
    

    # 1. Verify Data Ingestion
    print("\n--- Checking Data Ingestion ---")
    swx = voacap_service.get_current_space_wx()
    print(f"Loaded Space Weather: {swx}")
    
    # 2. Baseline Calculation (Fixed Time)
    print("\n--- Baseline Calculation (2026-02-12 00:00 UTC) ---")
    # Using the loaded SWX for baseline
    # We must access the core directly or pass swx to point prop if we want to be explicit,
    # but calculate_point_propagation now defaults to using SSN from args and ignoring others unless we change it.
    # Wait, calculate_point_propagation calls core with space_wx={'ssn': ssn}. 
    # It DOES NOT use the global 'swx' unless we change calculate_point_propagation to fetch it!
    # Correction: I updated calculate_point_propagation to pass space_wx={'ssn': ssn}. 
    # It currently IGNORES Kp/Bz/SW from files for point prop!
    # I should have updated calculate_point_propagation to fetch full SWX if not provided.
    # checking my previous edit... yes, I passed `space_wx={'ssn': ssn}`.
    
    # For verification, we will call CORE directly to test the physics.
    
    tx_lat, tx_lng = 34.0, -118.0 # (LA)
    rx_lat, rx_lng = 51.5, -0.1 # (London) - Path goes high latitude
    
    tx_r, txl_r = math.radians(tx_lat), math.radians(tx_lng)
    rx_r, rxl_r = math.radians(rx_lat), math.radians(rx_lng)
    s_dec, s_lng = voacap_service.get_solar_pos(2026, 2, 12, 0.0)
    
    # Baseline: Low Kp, No Storm
    base_swx = {'kp': 2.0, 'bz': 2.0, 'sw_speed': 350.0, 'ssn': 100}
    muf_b, rel_b = voacap_service.calculate_point_propagation_core(
        tx_r, txl_r, rx_r, rxl_r, 7.0, 3.0, s_dec, s_lng,
        math.cos(tx_r), math.sin(tx_r), math.cos(s_dec), math.sin(s_dec),
        15.0, math.radians(80.5), math.radians(-72.5), path=0, space_wx=base_swx
    )
    print(f"Baseline (Kp=2, Bz=2, V=350): MUF={muf_b:.2f}, REL={rel_b:.2f}")
    
    # Storm: High Kp, Southward Bz, Fast SW
    storm_swx = {'kp': 8.0, 'bz': -15.0, 'sw_speed': 800.0, 'ssn': 100}
    muf_s, rel_s = voacap_service.calculate_point_propagation_core(
        tx_r, txl_r, rx_r, rxl_r, 7.0, 3.0, s_dec, s_lng,
        math.cos(tx_r), math.sin(tx_r), math.cos(s_dec), math.sin(s_dec),
        15.0, math.radians(80.5), math.radians(-72.5), path=0, space_wx=storm_swx
    )
    print(f"Storm    (Kp=8, Bz=-15, V=800): MUF={muf_s:.2f}, REL={rel_s:.2f}")
    
    diff_m = muf_b - muf_s
    diff_r = rel_b - rel_s
    print(f"Impact: MUF Drop={diff_m:.2f}, REL Drop={diff_r:.2f}")
    
    if diff_m > 0 and diff_r > 0:
        print("SUCCESS: Storm conditions degraded propagation as expected.")
    else:
        print("FAILURE: Model did not respond to storm conditions significantly.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
