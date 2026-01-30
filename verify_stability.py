import requests
import threading
import time
import sys

# Define endpoints to test
ENDPOINTS = [
    "/fetchIPGeoloc.pl",
    "/fetchPSKReporter.pl?bycall=K1ABC&maxage=3600",
    "/fetchWSPR.pl?ofcall=K1ABC&maxage=3600",
    "/fetchRBN.pl?bycall=K1ABC&maxage=3600",
    "/geomag/kindex.txt",
    "/ssn/ssn-31.txt",
    "/solar-flux/solarflux-99.txt",
    "/xray/xray.txt",
    "/solar-wind/swind-24hr.txt",
    "/Bz/Bz.txt",
    "/aurora/aurora.txt",
    "/NOAASpaceWX/noaaswx.txt",
    "/NOAASpaceWX/rank2_coeffs.txt"
]

def test_endpoint(ep):
    url = f"http://localhost:8086{ep}"
    try:
        start = time.time()
        # Use a reasonable timeout
        resp = requests.get(url, timeout=12)
        end = time.time()
        duration = end - start
        
        status = "OK" if resp.status_code == 200 else "FAIL"
        content_len = len(resp.text)
        
        print(f"[{status}] {ep:50} | Status: {resp.status_code} | Time: {duration:5.2f}s | Len: {content_len}")
        
        if resp.status_code == 200 and content_len == 0 and "psk" not in ep.lower():
             print(f"      [WARNING] {ep} returned empty content!")
             
        return resp.status_code == 200
    except Exception as e:
        print(f"[ERROR] {ep:50} | {e}")
        return False

def main():
    print(f"{'Endpoint':55} | Result")
    print("-" * 80)
    
    all_ok = True
    threads = []
    results = []

    # Use threads for parallel testing (tests ThreadingTCPServer)
    for ep in ENDPOINTS:
        t = threading.Thread(target=lambda e=ep: results.append(test_endpoint(e)))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    if all(results) and len(results) == len(ENDPOINTS):
        print("\nAll endpoints responded successfully.")
    else:
        print("\nSome endpoints failed or returned errors.")
        sys.exit(1)

    print("\nVerification completed.")

if __name__ == "__main__":
    main()
