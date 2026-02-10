# HamClock Data Source Parity TODO

## High Priority: Truly Static/Shims
- [ ] Convert `/ham/HamClock/fetchBandConditions.pl` from shim to dynamic model (SSN/Solar Flux based).
- [ ] Implement dynamic routing for `/ham/HamClock/fetchONTA.pl` using `onta_service.py`.
- [ ] Implement dynamic routing for `/ham/HamClock/fetchAurora.pl` using `aurora.txt` (via `noaa_fetcher.py`).
- [ ] Implement dynamic routing for `/ham/HamClock/fetchDXPeds.pl` using `dxpeditions.txt` (via `dxped_service.py`).

## Medium Priority: Semi-Static (Upstream Copies)
- [ ] Localize `/ham/HamClock/worldwx/wx.txt` (generate local weather grid).
- [ ] Convert `/ham/HamClock/contests/contests311.txt` to local ingestion (e.g., WA7BNM).
- [ ] Calculate `/ham/HamClock/dst/dst.txt` locally from TZ database.
- [ ] Derive `/ham/HamClock/cty/cty_wt_mod-ll-dxcc.txt` from local `Big CTY` data.

## Investigation & Bug Fixes
- [ ] **Fix**: Integrate `drap_service.py` into `scheduler.py` or `noaa_fetcher.py` (Orphaned service).
- [ ] **Investigate**: Repair 0% parity for `/ham/HamClock/fetchVOACAPArea.pl`.
- [ ] **Investigate**: Repair 0% parity for `/ham/HamClock/SDO/*.bmp.z` (Check color/header/ImageMagick).
- [ ] **Investigate**: Repair 0% parity for `/ham/HamClock/solar-wind/swind-24hr.txt` (Check formatting/precision).

## Next Steps
1. Integrate orphan services (DRAP).
2. Implement dynamic model for Band Conditions.
3. Localize Weather Grid.
4. Refine Space Weather formatting for parity.
