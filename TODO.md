# HamClock Data Source Parity TODO

## High Priority: Truly Static/Shims
- [x] Convert `/ham/HamClock/fetchBandConditions.pl` from shim to dynamic model (SSN/Solar Flux based).
- [x] Implement dynamic routing for `/ham/HamClock/fetchONTA.pl` using `onta_service.py`.
- [x] Implement dynamic routing for `/ham/HamClock/fetchAurora.pl` using `aurora.txt` (via `noaa_fetcher.py`).
- [x] Implement dynamic routing for `/ham/HamClock/fetchDXPeds.pl` using `dxpeditions.txt` (via `dxped_service.py`).

## Medium Priority: Semi-Static (Upstream Copies)
- [x] Localize `/ham/HamClock/worldwx/wx.txt` (via `weather_grid_service.py`).
- [ ] Convert `/ham/HamClock/contests/contests311.txt` to local ingestion (e.g., WA7BNM).
- [ ] Ingest `/ham/HamClock/dst/dst.txt` (Disturbance Storm Time geomagnetic index) locally.
- [ ] Derive `/ham/HamClock/cty/cty_wt_mod-ll-dxcc.txt` from local `Big CTY` data.

## Investigation & Bug Fixes
- [x] **Fix**: Integrate `drap_service.py` into `noaa_fetcher.py` (Complete).
- [x] **Fix**: achieved 100% parity for `/ham/HamClock/fetchVOACAPArea.pl` (Raw pixels & Map 1 dimming).
- [x] **Investigate**: Repair 0% parity for `/ham/HamClock/SDO/*.bmp.z` (Header/Patch Fixed).
- [x] **Investigate**: Repair 0% parity for `/ham/HamClock/solar-wind/swind-24hr.txt` (Formatting Fixed).

## Next Steps
1. Implement local Dst (Disturbance Storm Time) index ingestion (Kyoto WDC).
2. Convert `/ham/HamClock/contests/contests311.txt` to local ingestion (WA7BNM).
3. Derive `/ham/HamClock/cty/cty_wt_mod-ll-dxcc.txt` from local Big CTY.
4. Address world weather parity issues (prevailing stats via `wttr.in`).
5. Improve SDO image scaling/quality for better parity.
