# Map Implementation Strategy: New Compliant Plans

These three strategies strictly adhere to the **No External Dependency** mandate. They all involve generating maps from **primary source data** (NOAA, NASA, Open-Meteo) locally on the backend, ensuring total sovereignty from the original HamClock infrastructure.

---

## Plan 1: The "Physics Engine" (Python Native)

**Concept:**
Implement a pure Python rendering pipeline using `numpy` and `PIL` (Pillow). This replicates the success of our existing `voacap_service.py` by performing mathematical calculations and array manipulations directly in Python code.

- **Primary Sources:** NOAA GRIB2 (Weather), NOAA SWPC JSON (Aurora).
- **Architecture:**
    1.  **Fetcher:** Downloads raw binary/JSON data from government servers.
    2.  **Processor:** Uses `numpy` to interpolate sparse grids into dense arrays (660x330).
    3.  **Renderer:** Uses `PIL` to map values to the specific HamClock color scales and generate BMP565 images.

| Feature | Assessment |
| :--- | :--- |
| **Complexity** | **High**. Requires implementing specific map projections (Plate Carrée) and interpolation logic manually. |
| **Benfits** | **Maximum Portability**. Runs anywhere Python runs. No external binaries required. Highly testable. |
| **Drawbacks** | Slower performance for heavy number crunching compared to compiled tools. |

---

## Plan 2: The "Compositor" (System Toolchain)

**Concept:**
Leverage high-efficiency system binaries like `ImageMagick` (`magick`), `gdal`, or `meteo-utils` to handle the heavy lifting of image manipulation and reprojection. Python acts merely as the orchestrator.

- **Primary Sources:** NASA GIBS (Satellite imagery), NOAA GeoColor (Clouds).
- **Architecture:**
    1.  **Fetcher:** Python script downloads high-res source images (e.g., full-disk satellite photos).
    2.  **Orchestrator:** Python constructs shell commands.
    3.  **Engine:** `ImageMagick` crops, resizes, reprojects, and composites layers (e.g., overlaying cloud layers on top of a static earth map).

| Feature | Assessment |
| :--- | :--- |
| **Complexity** | **Medium**. Complex shell commands, but less code to write. |
| **Benefits** | **Performance & Quality**. `Magick` is faster and has better resampling filters (Lanczos) than basic PIL. Best for visual maps (Clouds, SDO). |
| **Drawbacks** | **Runtime Dependency**. Requires `ImageMagick` and potentially `ffmpeg` installed on the host OS. |

---

## Plan 3: The "Aggregator" (Data Visualization)

**Concept:**
Generate "Meta-Maps" by visualizing the distinct data points we are *already collecting* for other features. Instead of fetching new map data, we turn our existing data streams into maps.

- **Primary Sources:** Internal `wx.txt` grid, Internal `dx_spots` database.
- **Architecture:**
    1.  **Weather Map:** Read our local `wx.txt` (which has 3,000+ data points). Create a heatmap interpolating these known points.
    2.  **Aurora Map:** Instead of the Ovation model, map real-time `k-index` and `Bz` weighted by latitude to show "Risk Zones".
    3.  **Renderer:** Use `matplotlib` (if available) or `scipy` to create contours/heatmaps from these discrete points.

| Feature | Assessment |
| :--- | :--- |
| **Complexity** | **Medium-High**. Data is sparse, so interpolation artifacts may occur. |
| **Benefits** | **Efficiency**. No new external network requests needed; reuses data we already have. highly cohesive system. |
| **Drawbacks** | **Low Resolution**. Maps will look "blocky" or smoothed compared to high-res satellite data. |

---

## Map Type Strategy Assessment

The following table evaluates the suitability of each plan for the specific map types identified in `docs/MAP_TYPES.md`.

| Map Type | Plan 1 (Physics) | Plan 2 (Compositor) | Plan 3 (Aggregator) | Recommended Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Countries** | N/A (Static) | N/A (Static) | N/A (Static) | **Static File** (Done) |
| **Terrain** | N/A (Static) | N/A (Static) | N/A (Static) | **Static File** (Done) |
| **DRAP** | **High**. Already implemented (`drap_service.py`). | Medium. Could composite NOAA images. | Low. Too complex for simple aggregation. | **Plan 1 (Physics)** - *Done* |
| **MUF-VCAP**| **High**. Already implemented (`voacap_service.py`). | Low. Dynamic user query. | Low. Too complex. | **Plan 1 (Physics)** - *Done* |
| **MUF-RT** | **High**. Fetch NOAA IONO grid JSON. Render. | Medium. Fetch IONO Map Image. | **Medium**. Interpolate local ionosonde data (already captured). | **Plan 1 (Physics)** - Better fidelity than Plan 3. |
| **Aurora** | **High**. Render NOAA Ovation grid JSON. | Medium. Composite NOAA Ovation images. | **Low**. Map Kp/Bz to simple zones. Too coarse. | **Plan 1 (Physics)** - Use NOAA JSON source. |
| **Weather** | High. Fetch GFS GRIB2. Complex parsing. | Low. Hard to find image with exact color scale. | **High**. We already have `wx.txt` grid! | **Plan 3 (Aggregator)** - Use existing `wx.txt`. |
| **TOA** | **High**. Dynamic VOACAP calc. | N/A. | N/A. | **Plan 1 (Physics)** - *Done* |
| **REL** | **High**. Dynamic VOACAP calc. | N/A. | N/A. | **Plan 1 (Physics)** - *Done* |
| **Clouds** | Low. Raw satellite data is massive/complex. | **High**. Composite NASA GIBS / NOAA GeoColor images. | N/A. No data points. | **Plan 2 (Compositor)** - Use `ImageMagick`. |
| **User** | N/A | N/A | N/A | **Direct Upload** |

---

## Strategic Recommendation Summary

1.  **Weather Map:** adopt **Plan 3 (Aggregator)**.
    -   We already have `weather_grid_service.py` populating `wx.txt` with thousands of live data points.
    -   Using `matplotlib` or `scipy.interpolate` to turn this into a heatmap is efficient and reuses existing sovereign data.

2.  **Aurora & MUF-RT:** adopt **Plan 1 (Physics Engine)**.
    -   The science data (JSON/Text grids) is small and easy to parse in Python.
    -   Rendering locally ensures we match the specific color scales required by the client.

3.  **Clouds:** adopt **Plan 2 (Compositor)**.
    -   Satellite imagery is visual by nature.
    -   Use `ImageMagick` to process high-res public domain images from NASA/NOAA, saving significant development time compared to raw data processing.
