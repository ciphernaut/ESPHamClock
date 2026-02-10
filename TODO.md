# HamClock Data Source Parity TODO

## High Priority: Truly Static/Shims
- [x] Convert `/ham/HamClock/fetchBandConditions.pl` from shim to dynamic model (SSN/Solar Flux based).
- [x] Implement dynamic routing for `/ham/HamClock/fetchONTA.pl` using `onta_service.py`.
- [x] Implement dynamic routing for `/ham/HamClock/fetchAurora.pl` using `aurora.txt` (via `noaa_fetcher.py`).
- [x] Implement dynamic routing for `/ham/HamClock/fetchDXPeds.pl` using `dxpeditions.txt` (via `dxped_service.py`).

## Medium Priority: Semi-Static (Upstream Copies)
- [x] Localize `/ham/HamClock/worldwx/wx.txt` (via `weather_grid_service.py`).
- [x] Convert `/ham/HamClock/contests/contests311.txt` to local ingestion (WA7BNM RSS).
- [x] Ingest `/ham/HamClock/dst/dst.txt` (Disturbance Storm Time geomagnetic index) locally.
- [x] Derive `/ham/HamClock/cty/cty_wt_mod-ll-dxcc.txt` from local `Big CTY` data.

## Investigation & Bug Fixes
- [x] **Fix**: Integrate `drap_service.py` into `noaa_fetcher.py` (Complete).
- [x] **Fix**: achieved 100% parity for `/ham/HamClock/fetchVOACAPArea.pl` (Raw pixels & Map 1 dimming).
- [x] **Fix**: Corrected band mapping (removed 60m) and implemented Long Path support in `voacap_service.py`.
- [x] **Fix**: Added night-time MUF floor to improve reliability on lower bands during darkness.
- [x] **Investigate**: Repair 0% parity for `/ham/HamClock/SDO/*.bmp.z` (Header/Patch Fixed).
- [x] **Investigate**: Repair 0% parity for `/ham/HamClock/solar-wind/swind-24hr.txt` (Formatting Fixed).

## REST API Parity & Reconciliation
- [x] Investigate Client Timezone mismatch (`UTC+0` vs `UTC+10` in Australia).
    - [x] identified root cause: missing newline in backend weather response.
    - [x] verified fix: `DE_tz` now correctly reports `UTC+10`.
- [x] **Fix**: achieved 100% parity for `get_spacewx.txt` (restored DRAP, Bz, and DEDX fields).
- [ ] Fine-tune VOACAP reliability peaks to match original server sensitivity.
- [ ] Implement Comprehensive Parity Test Suite using REST APIs (`proxy/compare_v2.py`).

## Next Steps
- [x] Address world weather parity issues (prevailing stats via `wttr.in`).
- [ ] Improve SDO image scaling/quality for better parity.
- [ ] Fully automate parity checking against the original server on port 8083.
