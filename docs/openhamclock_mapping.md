# OpenHamClock Data Source & Logic Mapping

This document provides a comprehensive mapping of the data sources and propagation logic used in the `openhamclock` project (a modern web-based reinterpretation of HamClock).

## 1. Overview
OpenHamClock utilizes a **Hybrid Propagation Model** that combines:
1.  **ITU-R P.533-14 (ITURHFProp)** for high-precision point-to-point predictions.
2.  **Real-time Ionosonde Data** (KC2G/GIRO) for "nowcast" corrections.
3.  **Local Empirical Models** for fast, large-scale heatmap generation.

## 2. Data Sources

| Data Type | Source Provider | Endpoint / Reference | Frequency |
| :--- | :--- | :--- | :--- |
| **Solar Flux (SFI)** | NOAA SWPC | `services.swpc.noaa.gov/json/f107_cm_flux.json` | 5 min |
| **Geomagnetic (K-Index)** | NOAA SWPC | `services.swpc.noaa.gov/products/noaa-planetary-k-index.json` | 5 min |
| **Ionosphere (foF2/MUF)** | KC2G / GIRO | `prop.kc2g.com/api/stations.json` | 10 min |
| **Propagation Engine** | ITURHFProp Service | `proppy-production.up.railway.app` (or self-hosted) | On-demand |
| **GeoIP** | ip-api.com | `ip-api.com/batch` | On-demand |

## 3. VOACAP DE-DX Path Data & Generation

The user-requested "VOACAP DE-DX" data corresponds to two distinct internal mechanisms in OpenHamClock:

### A. Point-to-Point Path (DE to DX)
**Endpoint:** `/api/propagation`
**Logic:** "Hybrid ITU-R P.533"
1.  **Solar Data Fetch:** Retrieves current SFI, SSN, and K-Index from NOAA.
2.  **Ionosphere Fetch:** Retrieves real-time ionosonde station data from KC2G.
3.  **Path Geometry:** Calculates Great Circle path, midpoint, and antimeridian crossings.
4.  **Midpoint Interpolation:** Uses Inverse Distance Weighting (IDW) to estimate `foF2` and `MUF(3000)` at the path midpoint using the nearest valid GIRO stations.
5.  **Engine Execution:** Calls the external `ITURHFProp` service (which runs the official ITU-R P.533-14 Fortran binary).
6.  **Hybrid Correction:** The engine's statistical prediction is adjusted (scaled) based on the real-time ionospheric midpoint data.
    *   *If ITURHFProp fails:* Falls back to a local JS calculation.

### B. Propagation Map (DE to World Grid)
**Endpoint:** `/api/propagation/heatmap`
**Logic:** "Enhanced Local Estimation"
Unlike the point-to-point path, the map **does not** query the external ITU engine for every grid cell due to performance constraints. Instead, it uses a highly optimized local JavaScript approximation:

1.  **Grid Generation:** Iterates over a user-defined grid (e.g., 10°x10°).
2.  **Local Calculation (`calculateEnhancedReliability`):**
    *   **MUF/LUF:** Estimated purely from solar indices (SFI/SSN) and hour (diurnal variation). *Does not use real-time ionosonde data for the map loops.*
    *   **Physics:** Simulates standard VOACAP-like logic:
        *   **Day/Night:** Frequency adjustments based on solar zenith.
        *   **Signal Margin:** Adds effective gain for Mode (CW/FT8 vs SSB) and Power.
        *   **Penalties:** Applies reductions for:
            *   Geomagnetic Storms (High K-Index).
            *   Auroral Zone paths (Lat > 60°).
            *   Multi-hop paths (distance decay).
3.  **Result:** Reliability percentage (0-100%) mapped to colors (Red/Yellow/Green).

## 4. Key Logic: `calculateEnhancedReliability`
Located in `glue/server.js`, this function approximates the VOACAP engine:
*   **Effective MUF:** `MUF_base * (1 + SignalMargin * 0.012)`
*   **Effective LUF:** `LUF_base * (1 - SignalMargin * 0.008)`
*   **Reliability Curve:**
    *   Peak reliability is at **85% of MUF** (Optimum Working Frequency).
    *   Reliability drops sharply above MUF or below LUF.

## 5. Attribution
*   **NOAA Space Weather Prediction Center** for solar data.
*   **KC2G** for the aggregated API of the **GIRO (Global Ionosphere Radio Observatory)** network.
*   **ITU (International Telecommunication Union)** for the P.533-14 propagation method.
*   **OpenHamClock Contributors** for the Node.js implementation of the hybrid logic.
