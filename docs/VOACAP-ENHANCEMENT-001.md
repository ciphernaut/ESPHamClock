# VOACAP Service Enhancement Plan (001)

## 1. Gap Analysis Summary

Based on comparisons between the legacy VOACAP model and the current Python "reboot" implementation (`voacap_service.py`), the following gaps require remediation:

| Feature | Current Status in Code | Missing / Required | Source Data Availability |
| :--- | :--- | :--- | :--- |
| **Solar Wind** | Not Used | Required to model ionospheric disturbance ($V_{sw}$). | **Available**: `noaa_fetcher.py` saves `solar-wind/swind-24hr.txt`. |
| **IMF (Bz)** | Not Used | Required for magnetosphere coupling (Bz < 0 triggers storms). | **Available**: `noaa_fetcher.py` saves `Bz/Bz.txt`. |
| **Geomagnetic Activity (Kp)** | Not Used | Required for storm degradation logic. | **Available**: `noaa_fetcher.py` saves `geomag/kindex.txt`. |
| **Geomagnetic Latitude** | Simplified | Needs accurate IGRF or dipole model for auroral zones. | **Partial**: Can improve using `geomag` lib or better math. |
| **Sporadic E (Es)** | Disabled | Needs `FPROB` or Es probability model. | **Partial**: `drap_service.py` has critical freq data. |
| **Antenna Gain / Noise** | Fixed Constants | Needs configurable gain/noise per band/path. | **None**: Needs new configuration/params. |

## 2. Technical Implementation

### A. Data Ingestion Integration
Update `voacap_service.py` to ingest the rich dataset already collected by `noaa_fetcher.py`.

-   **Load `geomag/kindex.txt`**: Read the most recent Kp index to adjust MUF/Loss.
    -   *Logic*: High Kp (> 4) should depress MUF and increase Auroral absorption.
-   **Load `solar-wind/swind-24hr.txt`**: Read current Solar Wind Speed ($V_{sw}$).
    -   *Logic*: High $V_{sw}$ (> 500 km/s) correlates with increased absorption/instability.
-   **Load `Bz/Bz.txt`**: Read current IMF Bz.
    -   *Logic*: Negative Bz (southward) significantly increases noise/absorption in polar paths.

### B. Physics Model Enhancements
Modify `calculate_point_propagation_core` to include these new terms.

1.  **Kp-Index Scaling**:
    ```python
    # Example adjustment
    muf_depression = 1.0 - (max(0, kp - 3) * 0.05) # 5% drop per Kp point above 3
    p_muf *= muf_depression
    ```
2.  **Auroral Absorption (Bz/Speed)**:
    -   Identify path intersection with Auroral Oval (already partially in `is_polar`).
    -   Expand `is_polar` logic to be dynamic based on Kp (Oval expands south with high Kp).
    -   Add `excess_absorption` term if path crosses Oval during negative Bz.

### C. Sporadic E Implementation
-   Re-enable and refine the `g_duct` (ducting) logic.
-   Link it to a season/time-of-day probability map or `drap` data if possible to simulate Es.

### D. Antenna & Noise Configuration
-   Add `TX_GAIN`, `RX_GAIN`, `SYS_NOISE` as query parameters to `generate_voacap_response`.
-   Use these to offset the `p_rel` (SNR) calculation.

## 3. Implementation Steps

1.  **Modify `voacap_service.py`**:
    -   Add `get_current_space_wx()` function to parse the text files.
    -   Inject `space_wx` dict into `calculate_grid_propagation_vectorized`.
2.  **Update Verification Script**:
    -   Update `verify_voacap.py` to print loaded Space Wx values to confirm ingestion.
3.  **Refine Model**:
    -   Iteratively tune the coefficients (e.g., how much Kp affects MUF) to match the "Original Upstream Map" visual benchmarks.

## 4. Verification Plan

### Automated Testing
-   Run `verify_voacap.py` before and after changes.
-   **Success Criteria**:
    -   Execution time remains acceptable (< 1s per map).
    -   Output `MUF`/`REL` values change when Kp input is manually mocked to high values (e.g., Kp=8).

### Visual Comparison
-   Generate maps with `Kp=0` vs `Kp=9`.
-   **Expectation**: Kp=9 map should show significantly reduced coverage (lower signal strength) and suppressed MUFs, especially in polar regions.
