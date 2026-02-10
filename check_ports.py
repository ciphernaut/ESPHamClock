import socket
import requests
import sys

PORTS = [
    (8001, "REST-1 (ax4test)"),
    (8002, "REST-2 (ax4upstream)"),
    (8091, "RW-1 (ax4test)"),
    (8092, "RW-2 (ax4upstream)"),
    (8081, "RO-1 (ax4test)"),
    (8082, "RO-2 (ax4upstream)"),
]

def check_port(port, label):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            result = s.connect_ex(('127.0.0.1', port))
            if result == 0:
                print(f"[OPEN]   {port}: {label}")
                return True
            else:
                print(f"[CLOSED] {port}: {label}")
                return False
    except Exception as e:
        print(f"[ERROR]  {port}: {label} - {e}")
        return False

def check_http(port, endpoint="/get_config.txt"):
    url = f"http://127.0.0.1:{port}{endpoint}"
    try:
        response = requests.get(url, timeout=2.0)
        print(f"  -> HTTP {response.status_code} ({len(response.text)} bytes)")
    except Exception as e:
        print(f"  -> HTTP FAILED: {e}")

print("Checking Ports...")
for port, label in PORTS:
    if check_port(port, label):
        if "REST" in label:
            check_http(port)
