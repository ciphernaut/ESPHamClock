import requests
import sys

def get_rest_data(port, endpoint):
    url = f"http://localhost:{port}/{endpoint}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def compare_voacap(data1, data2):
    lines1 = data1.strip().splitlines()
    lines2 = data2.strip().splitlines()
    
    if not lines1 or not lines2 or "Error" in data1 or "Error" in data2:
        print("Cannot compare VOACAP data.")
        return

    print(f"{'Band':<5} | {'My Server Col 0':<15} | {'Orig Server Col 0':<15} | {'Diff':<5}")
    print("-" * 50)
    
    for i in range(min(len(lines1), len(lines2))):
        if 'MHz' in lines1[i] and 'MHz' in lines2[i]:
            parts1 = lines1[i].split()
            parts2 = lines2[i].split()
            # Col 0 is the first number after the band label
            # Format: '10m    0  0 ...'
            val1 = parts1[1]
            val2 = parts2[1]
            try:
                diff = int(val1) - int(val2)
                print(f"{parts1[0]:<5} | {val1:>15} | {val2:>15} | {diff:>5}")
            except:
                pass

def main():
    MY_PORT = 8080
    ORIG_PORT = 8083

    endpoints = ["get_de.txt", "get_dx.txt", "get_config.txt", "get_voacap.txt"]

    print(f"Comparing HamClock on port {MY_PORT} (Mine) and {ORIG_PORT} (Original)\n")

    for ep in endpoints:
        print(f"=== {ep} ===")
        d1 = get_rest_data(MY_PORT, ep)
        d2 = get_rest_data(ORIG_PORT, ep)
        
        if ep == "get_voacap.txt":
            compare_voacap(d1, d2)
        else:
            # Simple line-by-line diff for small files
            l1 = d1.strip().splitlines()
            l2 = d2.strip().splitlines()
            for line1, line2 in zip(l1, l2):
                if line1 != line2:
                    print(f"MINE: {line1}")
                    print(f"ORIG: {line2}")
                    print()
        print()

if __name__ == "__main__":
    main()
