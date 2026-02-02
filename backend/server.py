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
    import sdo_service
    import drap_service
    import voacap_service
    logger.info("Successfully imported all Group 3 dynamic services")
except ImportError as e:
    logger.error(f"Failed to import services: {e}")
    # Print to stdout/stderr as well to ensure it's captured
    print(f"CRITICAL ERROR: {e}", file=sys.stderr)
    sys.exit(1)

PORT = 9086
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "processed_data")


class HamClockBackend(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

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
        elif normalized_path == "/fetchDRAP.pl":
            self.handle_drap(query)
        elif normalized_path in ["/fetchONTA.pl", 
                    "/fetchWordWx.pl", "/fetchAurora.pl", "/fetchDXPeds.pl"]:
            # Serve as static for now or implement shim
            self.handle_static(normalized_path)
        elif normalized_path.startswith("/SDO/"):
            self.handle_sdo(normalized_path)
        elif normalized_path.startswith("/geomag/") or normalized_path.startswith("/ssn/") or normalized_path.startswith("/solar-flux/") \
             or normalized_path.startswith("/xray/") or normalized_path.startswith("/solar-wind/") or normalized_path.startswith("/Bz/") \
             or normalized_path.startswith("/aurora/") or normalized_path.startswith("/dst/") or normalized_path.startswith("/NOAASpaceWX/") \
             or normalized_path.startswith("/drap/") or normalized_path.startswith("/cty/") or normalized_path.startswith("/ONTA/") \
             or normalized_path.startswith("/dxpeds/") or normalized_path.startswith("/contests/") \
             or normalized_path.endswith(".txt") or normalized_path.endswith(".bmp") or normalized_path.endswith(".bmp.z"):
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
                encoded_result = result.encode()
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", str(len(encoded_result)))
                self.end_headers()
                self.wfile.write(encoded_result)
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
            # e.g., /geomag/kindex.txt -> processed_data/geomag/kindex.txt
            
            # Remove leading slash for os.path.join
            rel_path = path.lstrip('/')
            local_path = os.path.join(DATA_DIR, rel_path)
            logger.debug(f"Static request for: {path} -> {local_path}")
            
            if os.path.exists(local_path):
                # Set content type based on extension
                content_type = "application/octet-stream" if local_path.endswith(".z") else "text/plain"
                with open(local_path, "rb") as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header("Content-type", content_type)
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    logger.debug(f"Served {local_path} ({len(content)} bytes)")
            else:
                logger.warning(f"Static file not found: {local_path}")
                self.send_error(404, f"File {rel_path} not found in {DATA_DIR}")
        except (BrokenPipeError, ConnectionResetError) as e:
            logger.warning(f"Client disconnected during static response: {e}")
        except Exception as e:
            logger.error(f"Error in handle_static: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_version(self, query):
        # Current HamClock version is 4.22
        # Original response is exactly 32 bytes including newlines
        # Format: "X.XX\nNo info for version  X.XX\n\n\n"
        # 4.22\n (5) + No info for version  4.22\n (24) + \n\n (2) = 31 bytes? 
        # Let's count carefully:
        # '4' '.' '2' '2' '\n' -> 5 bytes
        # 'N' 'o' ' ' 'i' 'n' 'f' 'o' ' ' 'f' 'o' 'r' ' ' 'v' 'e' 'r' 's' 'i' 'o' 'n' ' ' ' ' '4' '.' '2' '2' '\n' -> 26 bytes
        # 5 + 26 = 31 bytes.
        # Adding one more \n gives 32 bytes.
        version_text = "4.22\nNo info for version  4.22\n\n"
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", str(len(version_text)))
        self.end_headers()
        self.wfile.write(version_text.encode('utf-8'))

    def handle_voacap_area(self, query):
        try:
            logger.info(f"Generating dynamic VOACAP Area map for query: {query}")
            results = voacap_service.generate_voacap_response(query)
            if results and len(results) == 2:
                l1, l2 = len(results[0]), len(results[1])
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("X-2Z-lengths", f"{l1} {l2}")
                self.end_headers()
                self.wfile.write(results[0])
                self.wfile.write(results[1])
            else:
                self.send_error(500, "Failed to generate VOACAP maps")
        except Exception as e:
            logger.error(f"Error in handle_voacap_area: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_voacap_map(self, path):
        try:
            # Re-use area handler logic, might need adjustment for MUF/TOA specific query params
            # but usually they use the same parameters
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            # Ensure MHZ=0 for MUF
            if "MUF" in path:
                query['MHZ'] = ['0']
            
            logger.info(f"Generating dynamic VOACAP {path} map")
            results = voacap_service.generate_voacap_response(query)
            if results and len(results) == 2:
                l1, l2 = len(results[0]), len(results[1])
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("X-2Z-lengths", f"{l1} {l2}")
                self.end_headers()
                self.wfile.write(results[0])
                self.wfile.write(results[1])
            else:
                self.send_error(500, "Failed to generate VOACAP maps")
        except Exception as e:
            logger.error(f"Error in handle_voacap_map: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_rss(self, query):
        # Shim for RSS feed
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"HamClock Replacement Server Active - Local Source Feed Running\n")

    def handle_drap(self, query):
        try:
            # Stats for plots
            stats = drap_service.get_drap_stats()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(stats.encode())
        except Exception as e:
            logger.error(f"Error in handle_drap: {e}")
            self.send_error(500, str(e))

    def handle_world_wx(self):
        try:
            # Use the de-proxied original data if available
            sample_path = os.path.join(DATA_DIR, "worldwx/wx.txt")
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

    def handle_sdo(self, path):
        try:
            # SDO images are fetched and processed dynamically
            img_data = sdo_service.get_sdo_image(path)
            if img_data:
                logger.debug(f"Serving live SDO image for {path}")
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Content-Length", str(len(img_data)))
                self.end_headers()
                self.wfile.write(img_data)
            else:
                self.send_error(404, "SDO image fetch failed")
        except Exception as e:
            logger.error(f"Error in handle_sdo: {e}")
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

            encoded_formatted = formatted.encode('utf-8')
            logger.debug(f"Sending weather data ({len(encoded_formatted)} bytes)")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", str(len(encoded_formatted)))
            self.end_headers()
            self.wfile.write(encoded_formatted)
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
