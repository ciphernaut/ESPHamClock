import http.server
import socketserver
import urllib.parse
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add ingestion directory to path to import services
ingestion_dir = os.path.join(os.path.dirname(__file__), "ingestion")
sys.path.append(ingestion_dir)
logger.debug(f"Added {ingestion_dir} to sys.path")

try:
    import geoloc_service
    import spot_service
    import weather_service
    logger.info("Successfully imported geoloc_service, spot_service, and weather_service")
except ImportError as e:
    logger.error(f"Failed to import services: {e}")
    # Print to stdout/stderr as well to ensure it's captured
    print(f"CRITICAL ERROR: {e}", file=sys.stderr)
    sys.exit(1)

PORT = 9086
DATA_DIR = "processed_data"


class HamClockBackend(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        # Normalize path: remove potential prefixes like /ham/HamClock/
        normalized_path = path
        if path.startswith("/ham/HamClock"):
            normalized_path = path[len("/ham/HamClock"):]
        
        print(f"Server received: {path} (normalized: {normalized_path}) with params {query}")

        if normalized_path == "/fetchIPGeoloc.pl":
            self.handle_geoloc(query)
        elif normalized_path == "/fetchPSKReporter.pl":
            self.handle_psk(query)
        elif normalized_path == "/version.pl":
            self.handle_version(query)
        elif normalized_path == "/RSS/web15rss.pl":
            self.handle_rss(query)
        elif normalized_path == "/wx.pl":
            self.handle_weather(query)
        elif normalized_path == "/worldwx/wx.txt":
            self.handle_world_wx()
        elif normalized_path == "/fetchVOACAPArea.pl":
            self.handle_voacap_area(query)
        elif normalized_path == "/fetchBandConditions.pl":
            self.handle_band_conditions(query)
        elif normalized_path in ["/fetchVOACAP-MUF.pl", "/fetchVOACAP-TOA.pl"]:
            self.handle_voacap_map(normalized_path)
        elif normalized_path in ["/fetchONTA.pl", "/fetchDRAP.pl",
                    "/fetchWordWx.pl", "/fetchAurora.pl", "/fetchDXPeds.pl"]:
            # Serve as static for now or implement shim
            self.handle_static(normalized_path)
        elif normalized_path.startswith("/SDO/"):
            self.handle_sdo(normalized_path)
        elif normalized_path.startswith("/geomag/") or normalized_path.startswith("/ssn/") or normalized_path.startswith("/solar-flux/") \
             or normalized_path.startswith("/xray/") or normalized_path.startswith("/solar-wind/") or normalized_path.startswith("/Bz/") \
             or normalized_path.startswith("/aurora/") or normalized_path.startswith("/dst/") or normalized_path.startswith("/NOAASpaceWX/") \
             or normalized_path.endswith(".txt"):
            # Serve from processed_data
            self.handle_static(normalized_path)
        else:
            self.send_error(404, "Not Found")

    def handle_geoloc(self, query):
        try:
            ip = query.get('ip', [None])[0]
            logger.debug(f"Geoloc request for IP: {ip}")
            result = geoloc_service.get_geoloc(ip)
            if result:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(result.encode())
            else:
                logger.warning(f"Geolocation failed for IP: {ip}")
                self.send_error(500, "Geolocation failed")
        except (BrokenPipeError, ConnectionResetError) as e:
            logger.warning(f"Client disconnected during geoloc response: {e}")
        except Exception as e:
            logger.error(f"Error in handle_geoloc: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_psk(self, query, mode=None):
        try:
            # HamClock sends 'of' or 'by' prefix.
            # bycall=... -> DE is sender
            # ofcall=... -> DE is receiver
            
            call = query.get('bycall', [None])[0] or query.get('call', [None])[0]
            grid = query.get('bygrid', [None])[0] or query.get('grid', [None])[0]
            is_receiver = False
            
            if not call and not grid:
                call = query.get('ofcall', [None])[0]
                grid = query.get('ofgrid', [None])[0]
                is_receiver = True
                
            maxage = int(query.get('maxage', [1800])[0])
            logger.debug(f"PSK request: call={call}, grid={grid}, is_receiver={is_receiver}")
            
            result = spot_service.fetch_pskreporter(callsign=call, grid=grid, maxage_sec=maxage, 
                                                    mode_filter=mode, is_receiver=is_receiver)
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(result.encode())
        except (BrokenPipeError, ConnectionResetError) as e:
            logger.warning(f"Client disconnected during PSK response: {e}")
        except Exception as e:
            logger.error(f"Error in handle_psk: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_static(self, path):
        try:
            # Map path to local file in DATA_DIR
            # e.g., /geomag/kindex.txt -> processed_data/kindex.txt
            # e.g., /ssn-31.txt -> processed_data/ssn-31.txt
            
            filename = os.path.basename(path)
            local_path = os.path.join(DATA_DIR, filename)
            logger.debug(f"Static request for: {path} -> {local_path}")
            
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(content)
            else:
                logger.warning(f"Static file not found: {local_path}")
                self.send_error(404, f"File {filename} not found in {DATA_DIR}")
        except (BrokenPipeError, ConnectionResetError) as e:
            logger.warning(f"Client disconnected during static response: {e}")
        except Exception as e:
            logger.error(f"Error in handle_static: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_version(self, query):
        # Current HamClock version is 4.22
        # Original response is exactly 32 bytes including newlines
        version_text = "4.22\nNo info for version  4.22\n\n\n\n"
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(version_text.encode('utf-8'))

    def handle_world_wx(self):
        try:
            sample_path = os.path.join(DATA_DIR, "worldwx_wx_sample.txt")
            if os.path.exists(sample_path):
                logger.info(f"Serving World Weather shim from {sample_path}")
                with open(sample_path, "rb") as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(content)
            else:
                self.send_error(404, "World weather sample not found")
        except Exception as e:
            logger.error(f"Error in handle_world_wx: {e}")
            self.send_error(500, str(e))

    def handle_band_conditions(self, query):
        try:
            sample_path = os.path.join(DATA_DIR, "band_conditions_sample.txt")
            if os.path.exists(sample_path):
                logger.info(f"Serving Band Conditions shim from {sample_path}")
                with open(sample_path, "rb") as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(content)
            else:
                self.send_error(404, "Band conditions sample not found")
        except Exception as e:
            logger.error(f"Error in handle_band_conditions: {e}")
            self.send_error(500, str(e))

    def handle_rss(self, query):
        # Shim for RSS feed
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"HamClock Replacement Server Active - Local Source Feed Running\n")

    def handle_voacap_area(self, query):
        try:
            # For now, serve the saved sample with fixed heights
            # Original: 660x330 (WIDTH=660, HEIGHT=330)
            sample_path = os.path.join(DATA_DIR, "voacap_area_sample.bin")
            lengths = "50546 37692"
            
            if os.path.exists(sample_path):
                logger.info(f"Serving VOACAP Area shim data from {sample_path}")
                with open(sample_path, "rb") as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header("Content-type", "application/octet-stream")
                    self.send_header("X-2Z-lengths", lengths)
                    self.end_headers()
                    self.wfile.write(content)
            else:
                logger.warning(f"VOACAP Area sample not found at {sample_path}")
                self.send_error(404, "VOACAP sample not available")
        except (BrokenPipeError, ConnectionResetError) as e:
            logger.warning(f"Client disconnected during VOACAP response: {e}")
        except Exception as e:
            logger.error(f"Error in handle_voacap_area: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_sdo(self, path):
        try:
            # SDO images are compressed .bmp.z
            # Map all to one sample for now
            sample_path = os.path.join(DATA_DIR, "sdo_sample.bmp.z")
            if os.path.exists(sample_path):
                logger.info(f"Serving SDO shim ({path}) from {sample_path}")
                with open(sample_path, "rb") as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header("Content-type", "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(content)
            else:
                self.send_error(404, "SDO sample not found")
        except Exception as e:
            logger.error(f"Error in handle_sdo: {e}")
            self.send_error(500, str(e))

    def handle_voacap_map(self, path):
        try:
            # For MUF/TOA, they use the same binary format
            sample_name = "voacap_muf_sample.bin" if "MUF" in path else "voacap_toa_sample.bin"
            sample_path = os.path.join(DATA_DIR, sample_name)
            
            # If specific sample doesn't exist, fallback to Area sample but maybe log it
            if not os.path.exists(sample_path):
                sample_path = os.path.join(DATA_DIR, "voacap_area_sample.bin")
            
            # MUF/TOA also need lengths, often similar to Area
            lengths = "50546 37692" # Fallback if unknown
            
            if os.path.exists(sample_path):
                logger.info(f"Serving VOACAP Map shim ({path}) from {sample_path}")
                with open(sample_path, "rb") as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header("Content-type", "application/octet-stream")
                    self.send_header("X-2Z-lengths", lengths)
                    self.end_headers()
                    self.wfile.write(content)
            else:
                self.send_error(404, "VOACAP map sample not available")
        except Exception as e:
            logger.error(f"Error in handle_voacap_map: {e}")
            self.send_error(500, str(e))

    def handle_weather(self, query):
        try:
            lat = float(query.get('lat', [0])[0])
            lng = float(query.get('lng', [0])[0])
            logger.debug(f"Weather request for lat={lat}, lng={lng}")
            raw_data = weather_service.fetch_weather(lat, lng)
            formatted = weather_service.format_for_hamclock(raw_data, lat, lng)
            
            if not formatted:
                logger.warning(f"Weather formatting returned empty for {lat}, {lng}. Sending error.")
                self.send_error(500, "Weather formatting failed")
                return

            logger.debug(f"Sending weather data ({len(formatted)} bytes)")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(formatted.encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError) as e:
            logger.warning(f"Client disconnected during weather response: {e}")
        except Exception as e:
            logger.error(f"Error in handle_weather: {e}", exc_info=True)
            self.send_error(500, str(e))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    with ThreadedTCPServer(("127.0.0.1", PORT), HamClockBackend) as httpd:
        print(f"HamClock Replacement Server running on port {PORT}")
        httpd.serve_forever()
