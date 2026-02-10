# OpenHamClock VOACAP Integration Plans

This document outlines three distinct strategies for integrating or supplanting the current `ESPHamClock` DE-DX VOACAP calculations with the methodologies used in `OpenHamClock`.

## Current State
*   **Our Implementation:** `backend/ingestion/voacap_service.py` uses a custom Python/NumPy implementation of VOACAP-like equations (`calculate_point_propagation_core`). It relies primarily on **Simulated/Predicted SSN** and Solar Flux.
*   **OpenHamClock:** Uses a **Hybrid Model**.
    *   *Point-to-Point:* Calls an external **ITU-R P.533-14** service (Fortran binary) + **Real-time Ionosonde Data** (KC2G).
    *   *Map:* Uses a local JavaScript estimation (`calculateEnhancedReliability`) for performance.

---

## Plan A: The "Sidecar" Service (High Precision)
**Concept:** Deploy the `iturhfprop-service` (from OpenHamClock) as a Docker container alongside our stack and offload all DE-DX point calculations to it.

### Implementation
1.  Add `iturhfprop-service` to our `docker-compose.yml` or `run_stack.sh`.
2.  Modify `backend/ingestion/voacap_service.py` to replace `calculate_point_propagation` with a REST call to `http://iturhfprop:3000/api/predict`.
3.  (Optional) Implement the Ionosonde fetcher (`prop.kc2g.com`) in Python to pass real-time parameters to the service, or trust the service's defaults if it handles it.

### Benefits
*   **Accuracy:** Uses the official ITU-R P.533-14 engine (Fortran), considered the "Gold Standard" for HF propagation.
*   **Parity:** Zero-effort parity with OpenHamClock's DE-DX numbers.
*   **Simplicity:** Removes complex math maintenance from our Python codebase.

### Drawbacks
*   **Deployment:** Adds a new service/container (memory/CPU overhead).
*   **Latency:** HTTP round-trip vs. in-process function call (~10ms vs ~0.1ms).
*   **Dependency:** Failure of the sidecar breaks band conditions.

---

## Plan B: The "Native Port" (High Performance)
**Concept:** Translate OpenHamClock's optimized JavaScript logic (`calculateEnhancedReliability` and `fetchIonosondeData`) directly into our Python `voacap_service.py`.

### Implementation
1.  Analyze `server.js` lines 5677-5776 (`calculateEnhancedReliability`).
2.  Rewrite this logic in Python, replacing our current `calculate_point_propagation_core`.
3.  Implement a `IonosondeService` in Python to fetch `prop.kc2g.com` data and cache it.
4.  Feed real-time `foF2` and `MUF` into the new Python function.

### Benefits
*   **Performance:** Python/NumPy execution is fast and stays in-process. No network overhead for calculations.
*   **Independence:** No external sidecar container required.
*   **Hybrid Accuracy:** Brings us closer to "Hybrid" model accuracy (using Ionosonde data) without the weight of the full ITU engine.

### Drawbacks
*   **Effort:** Significant coding work to port and verify the logic.
*   **Approximation:** It is still an *estimation* (JavaScript port), not the official ITU engine. Will not match Plan A's precision.

---

## Plan C: The "Ionosonde Augmentation" (Low Effort Enhancement)
**Concept:** Keep our existing `voacap_service.py` math (which is already a decent VOACAP approximation) but **feed it better data**.

### Implementation
1.  Create `backend/ingestion/ionosonde_service.py` to fetch real-time data from `prop.kc2g.com`.
2.  Update `voacap_service.py` to accept `ionosonde` data.
3.  Modify our existing `calculate_point_propagation_core` to:
    *   Use real `MUF` from ionosonde if available (instead of calculating from SSN).
    *   Adjust `foF2` based on real-time readings.
4.  Leave the core math mostly as-is, just overriding the solar input variables with real-world observed values.

### Benefits
*   **Minimal Change:** Leverages existing, working code.
*   **Better Data:** "Garbage in, garbage out" — better inputs (Ionosonde) will yield better outputs even with the current model.
*   **Safety:** Lowest risk of breaking existing functionality.

### Drawbacks
*   **Legacy Math:** We keep our custom, complex Python math which might differ from modern ITU standards.
*   **Unknown Accuracy:** We don't know if our current model reacts correctly to direct Ionosonde inputs (it might be tuned for SSN).

---

## Recommendation
**Plan B (Native Port)** offers the best balance for this project.
*   It aligns us with OpenHamClock's "Hybrid" logic (using real data).
*   It keeps the stack lightweight (no extra containers).
*   It significantly improves accuracy over pure SSN predictions.
