# Remaining Tasks for HamClock Parity - COMPLETED

## Weather Service Parity
- [x] Implement `get_prevailing_stats()` in `weather_service.py` to support `fetchWordWx.pl`.
- [x] Implement dynamic generation/fetch of `worldwx/wx.txt` (gridded weather data).
- [x] Update `server.py` to route `fetchWordWx.pl` and `fetchWorldWx.pl` to the dynamic service.
- [x] Investigate if `clearskyinstitute.com` grid can be proxied or fetched periodically (Implemented via `noaa_fetcher.py`).

## VOACAP Enhancement
- [x] Verify that base map files (`map-D-660x330-Countries.bmp`, `map-D-660x330-Terrain.bmp`) are correctly loaded in `voacap_service.py`.
- [x] Visually confirm TOA/MUF maps on the client have visible country borders.

## Backend Stability & Parity
- [x] Fix any remaining 502 errors for VOACAP endpoints.
- [x] Final sweep of `discrepancies.log` for high-significance items.
- [x] Verify `drap/stats.txt` history length and uniqueness is maintained in production.

## Verification
- [x] Run full stack and check client UI for:
    - [x] Dynamic weather updates (DE/DX and World map).
    - [x] Accurate VOACAP maps with textures.
    - [x] No 'DRAP data invalid' errors.
