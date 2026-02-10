# ESPHamClock Community Beta Guide 📡

Welcome to the ESPHamClock Reconstruction Beta! This repository provides a local backend replacement for HamClock data services.

## Quick Start (Verification Stack)

This environment runs two HamClock instances for live parity verification:

1.  **Start Services**:
    ```bash
    ./run_stack.sh restart all
    ```
    This starts the **Backend**, **Dual Proxies**, and **Dual Clients**.

2.  **Access the Clients**:
    -   **ax4test (DUT)**: `http://localhost:8091` (Compares local backend vs upstream)
    -   **ax4upstream (Original)**: `http://localhost:8092` (Baseline for comparison)

## Understanding the Dual-Client Setup

We run two clients in parallel to identify discrepancies immediately:
-   **ax4test**: Points to `localhost:9085` (Shadow Proxy). It uses our local backend but falls back to the original if data is missing.
-   **ax4upstream**: Points to `localhost:9095` (Verify Proxy). It provides a baseline for what the original server is currently serving.

## Monitoring Parity

Visit the Parity Dashboards to see real-time comparisons:
-   **ax4test vs Upstream**: `http://localhost:9085/parity`
-   **ax4upstream vs Upstream**: `http://localhost:9095/parity` (Should be 100% parity)

## Reporting Discrepancies

Check `logs/parity_summary.json` or the dashboard. If you see persistent "Diff" status for endpoints you care about, please share your `logs/proxy.log` with the development team!

## Project Layout
- `server.py`: The local backend shimming service.
- `shadow_proxy/`: The intelligent monitoring layer.
- `ingestion/`: Background fetchers that keep data fresh.
- `logs/`: Diagnostic output for community debugging.
