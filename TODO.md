# ESPHamClock Reconstruction TODO 📡

## Group 1: Foundation (Completed)
- [x] Create local backend `server.py` to shim basic endpoints.
- [x] Implement `ingestion/noaa_fetcher.py` for core solar/geomagnetic data.
- [x] Implement `ingestion/weather_service.py` using wttr.in.
- [x] Deploy `shadow_proxy/` for parity monitoring and fallback.
- [x] Basic service management with `run_stack.sh`.

## Group 2: Inaccurate Data Sources (In Progress)
- [x] Improve SSN/Solar Flux window accuracy in `noaa_fetcher.py`.
- [x] Align KP-Index (kindex.txt) 72-value window for exact match.
- [x] Fix X-Ray sampling intervals and formatting.
- [x] Map weather condition labels (Clear, Rain, Sunny) to match original backend format.
- [/] Verify Group 2 parity improvements on dashboard.

## Group 3: Dynamic Data Generation (Completed with Issues)
- [x] Replace static `voacap_area_sample.bin` with dynamic VOACAP calculations.
- [x] Fetch/generate live SDO imagery instead of `sdo_sample.bmp.z`.
- [x] Implement full logic for `fetchPSKReporter.pl` with callsign/grid filtering.
- [x] Implement `fetchDRAP.pl` logic for absorption maps.

## Active Priority Issues (Parity Fixes) ⚠️
- [ ] **SDO Imagery**: "File not BMP" error for wavelengths (e.g., so4A). Investigate header/compression.
- [ ] **Solar Wind (Bz/Bt)**: "BvBT data invalid" error. Verify JSON parsing and data formatting.
- [ ] **Aurora**: "arora data invalid" error. Check `aurora/` endpoint data structure.
- [ ] **Solar Flux**: "Solar Fluix data invalid" error. Verify `solarflux-99.txt` formatting.
- [ ] **World Weather (DX Wx)**: Incorrect prevailing stats. Compare against `DE Wx` logic.

## Group 4: Polish & Parity (Continuous)
- [ ] Achieve 95%+ parity on all critical text-based data files.
- [ ] Optimize ingestion scheduler for reliability and rate limiting.
- [ ] Improve documentation for community setup on Raspberry Pi/Docker.
- [ ] Exhaustive stability test with real ESP8266/ESP32 HamClock devices.
