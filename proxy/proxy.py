import http.server
import http.client
import socketserver
import os
import datetime
import hashlib
import difflib

PORT = 9085
TARGET_HOST = "clearskyinstitute.com"
LOCAL_REPLACEMENT_HOST = "localhost"
LOCAL_REPLACEMENT_PORT = 9086
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "backend", "data", "captured_data")
DISCREPANCY_LOG = os.path.join(BASE_DIR, "logs", "discrepancies.log")

# Proxy Modes:
# ORIGINAL: Only original backend
# SHADOW: Both, Serve Local (fallback to Original if local fails), Log discrepancies
# VERIFY: Both, Serve Original, Log discrepancies
# EXCLUSIVE: Only local backend
PROXY_MODE = os.environ.get("PROXY_MODE", "SHADOW").upper()

PARITY_SUMMARY = os.path.join(BASE_DIR, "logs", "parity_summary.json")
import json

class ShadowProxy(http.server.SimpleHTTPRequestHandler):
    def update_parity_summary(self, path, match):
        try:
            log_dir = os.path.dirname(PARITY_SUMMARY)
            if not os.path.exists(log_dir): os.makedirs(log_dir)
            summary = {}
            if os.path.exists(PARITY_SUMMARY):
                with open(PARITY_SUMMARY, "r") as f:
                    summary = json.load(f)
            
            # Normalize path for grouping (remove query params)
            base_path = path.split('?')[0]
            
            # Retrieve existing stats from nested structure or use defaults
            entry = summary.get(base_path, {})
            stats = entry.get("_stats", {"matches": 0, "total": 0})
            
            stats["total"] += 1
            if match: stats["matches"] += 1
            
            # Store detailed parity info for the dashboard
            summary[base_path] = {
                "status": "Match" if match else "Diff",
                "parity": f"{stats['matches']}/{stats['total']}",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "_stats": stats
            }
            
            with open(PARITY_SUMMARY, "w") as f:
                json.dump(summary, f, indent=4)
        except Exception as e:
            print(f"  [SUMMARY] Error: {e}")

    def fetch_from_backend(self, host, port, timeout, path, headers):
        try:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
            # Remove host header to avoid conflicts
            clean_headers = {key: val for key, val in headers.items() if key.lower() != 'host'}
            conn.request("GET", path, headers=clean_headers)
            response = conn.getresponse()
            data = response.read()
            status = response.status
            resp_headers = response.getheaders()
            conn.close()
            return status, resp_headers, data
        except Exception as e:
            return 502, [], str(e).encode()

    def do_GET(self):
        if self.path == "/parity":
            self.handle_parity()
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"[{timestamp}] Incoming Request ({PROXY_MODE}): {self.path}")
        
        orig_status, orig_headers, orig_data = 0, [], b""
        local_status, local_headers, local_data = 0, [], b""

        # 1. Fetch from Original if needed
        if PROXY_MODE in ["ORIGINAL", "SHADOW", "VERIFY"]:
            orig_status, orig_headers, orig_data = self.fetch_from_backend(TARGET_HOST, 80, 10, self.path, self.headers)
            if PROXY_MODE == "ORIGINAL":
                print(f"  [ORIGINAL MODE] Status: {orig_status} ({len(orig_data)} bytes)")
                self.send_backend_response(orig_status, orig_headers, orig_data)
                return
            print(f"  [ORIGINAL BACKEND] Status: {orig_status} ({len(orig_data)} bytes)")

        # 2. Fetch from Local if needed
        if PROXY_MODE in ["EXCLUSIVE", "SHADOW", "VERIFY"]:
            local_status, local_headers, local_data = self.fetch_from_backend(LOCAL_REPLACEMENT_HOST, LOCAL_REPLACEMENT_PORT, 5, self.path, self.headers)
            if PROXY_MODE == "EXCLUSIVE":
                print(f"  [EXCLUSIVE MODE] Status: {local_status} ({len(local_data)} bytes)")
                self.send_backend_response(local_status, local_headers, local_data)
                return
            print(f"  [LOCAL SERVER] Status: {local_status} ({len(local_data)} bytes)")

        # 3. Log and Compare for Shadow/Verify modes
        if PROXY_MODE in ["SHADOW", "VERIFY"]:
            self.log_capture(self.path, orig_status, orig_headers, orig_data)
            self.compare_responses(self.path, orig_status, orig_data, local_status, local_data)

        # 4. Decide what to serve
        if PROXY_MODE == "SHADOW":
            # Serve local, but fallback to original if local failed (404/500/502)
            if local_status >= 400 or local_status == 0:
                print(f"  [SHADOW] LOCAL failed ({local_status}), falling back to ORIGINAL")
                self.send_backend_response(orig_status, orig_headers, orig_data)
            else:
                self.send_backend_response(local_status, local_headers, local_data)
        elif PROXY_MODE == "VERIFY":
            # Serve original
            self.send_backend_response(orig_status, orig_headers, orig_data)

    protocol_version = "HTTP/1.0"

    def send_backend_response(self, status, headers, data):
        try:
            self.send_response(status)
            for key, val in headers:
                if key.lower() not in ['content-length', 'transfer-encoding', 'connection']:
                    self.send_header(key, val)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_capture(self, path, status, headers, data):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
            
        safe_path = path.replace("/", "_").replace("?", "_").replace("&", "_").strip("_")
        if not safe_path: safe_path = "root"
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Save as .bin for binary safety
        filename = f"{timestamp}_{safe_path}.bin"
        log_path = os.path.join(LOG_DIR, filename)
        
        try:
            with open(log_path, "wb") as f:
                header_text = f"Path: {path}\nStatus: {status}\nHeaders: {dict(headers)}\n\n--- DATA ---\n"
                f.write(header_text.encode('utf-8'))
                f.write(data)
        except Exception as e:
            print(f"  [LOG] Failed to save binary capture: {e}")

    def compare_responses(self, path, orig_status, orig_data, local_status, local_data):
        match = (orig_status == local_status and orig_data == local_data)
        self.update_parity_summary(path, match)

        if not match:
            # Noise filtering: Ignore if it's dynamic data and we expected drift
            dynamic_keywords = ["PSKReporter", "WSPR", "RBN", "wx.pl", "xray.txt"]
            is_dynamic = any(x in path for x in dynamic_keywords)
            
            with open(DISCREPANCY_LOG, "a") as f:
                f.write(f"--- DISCREPANCY DETECTED [{datetime.datetime.now()}] ---\n")
                f.write(f"Path: {path}\n")
                f.write(f"Status: ORIGINAL={orig_status}, LOCAL={local_status}\n")
                
                if is_dynamic:
                    f.write("Significance: LOW (Dynamic Data)\n")
                else:
                    f.write("Significance: HIGH (Potential Regression)\n")
                
                if orig_data != local_data:
                    f.write(f"Size: ORIGINAL={len(orig_data)}, LOCAL={len(local_data)}\n")
                    try:
                        orig_text = orig_data.decode('utf-8', errors='replace').splitlines()
                        local_text = local_data.decode('utf-8', errors='replace').splitlines()
                        diff = difflib.unified_diff(orig_text, local_text, fromfile="ORIGINAL", tofile="LOCAL")
                        f.write("Data Diff:\n")
                        for line in diff:
                            f.write(line + "\n")
                    except Exception as e:
                        f.write(f"Binary difference detected (cannot diff text: {e})\n")
                f.write("-" * 40 + "\n")

    def handle_parity(self):
        try:
            html = "<html><head><title>HamClock Parity Dashboard</title>"
            html += "<style>body{font-family:sans-serif;background:#1a1a1a;color:#eee;padding:20px;}"
            html += "table{border-collapse:collapse;width:100%;}th,td{padding:12px;text-align:left;border-bottom:1px solid #444;}"
            html += "th{background:#333;}.match{color:#4caf50;}.diff{color:#f44336;}</style></head><body>"
            html += "<h1>📡 HamClock Parity Dashboard (Proxy View)</h1>"
            
            if os.path.exists(PARITY_SUMMARY):
                with open(PARITY_SUMMARY, "r") as f:
                    data = json.load(f)
                
                html += "<table><tr><th>Endpoint</th><th>Last Result</th><th>Parity (Matches/Total)</th><th>Last Checked</th></tr>"
                for endpoint, info in data.items():
                    parity_class = "match" if info.get('status') == "Match" else "diff"
                    html += f"<tr><td>{endpoint}</td><td class='{parity_class}'>{info.get('status')}</td>"
                    html += f"<td>{info.get('parity')}</td>"
                    html += f"<td>{info.get('timestamp')}</td></tr>"
                html += "</table>"
            else:
                html += "<p>No parity data collected yet.</p>"
            
            html += "</body></html>"
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ThreadedTCPServer(("127.0.0.1", PORT), ShadowProxy) as httpd:
        print(f"Data Shadow Proxy running on port {PORT}")
        print(f"Forwarding to {TARGET_HOST} and comparing with {LOCAL_REPLACEMENT_HOST}:{LOCAL_REPLACEMENT_PORT}")
        httpd.serve_forever()

