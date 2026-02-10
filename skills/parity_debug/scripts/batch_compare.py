import sys
import subprocess
import os

ENDPOINTS = [
    "/get_spacewx.txt",
    "/get_de.txt",
    "/get_dx.txt",
    "/fetchBandConditions.pl",
    "/fetchONTA.pl",
    "/fetchAurora.pl",
    "/fetchDXPeds.pl",
]

REST_PORT1 = 8001
REST_PORT2 = 8002

def main():
    print(f"--- Parity Inspector: Batch Verification Sweep ---")
    results = []
    
    # Get the directory where compare_endpoint.py is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    compare_script = os.path.join(script_dir, "compare_endpoint.py")
    
    for ep in ENDPOINTS:
        url1 = f"http://localhost:{REST_PORT1}{ep}"
        url2 = f"http://localhost:{REST_PORT2}{ep}"
        
        print(f"Checking {ep}...")
        cmd = [
            "python3", compare_script,
            url1, url2, ep
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"  [OK]")
                results.append((ep, "OK"))
            else:
                print(f"  [DISCREPANCY]")
                results.append((ep, "DIFF"))
                # Print details if there's a diff
                print(res.stdout)
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append((ep, f"ERROR: {e}"))
            
    print("\n--- Summary Report ---")
    for ep, status in results:
        print(f"{ep:30} : {status}")

if __name__ == "__main__":
    main()
