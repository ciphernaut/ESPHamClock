# ESPHamClock Community Beta Guide 📡

Welcome to the ESPHamClock Reconstruction Beta! This repository provides a local backend replacement for HamClock data services.

## Quick Start (Backend Services)

If you are running this on a central server for your ESP8266/ESP32 devices:

1.  **Start Services**:
    ```bash
    ./run_stack.sh
    ```
    This starts the **Local Server**, **Data Scheduler**, and **Shadow Proxy**.

2.  **Point your HamClock at this server**:
    Configure your HamClock device to use your server's IP and Port **9085**.

## Understanding "Shadow mode"

By default, we run in **SHADOW** mode. 
- **Privacy**: Your device talks to your local server first.
- **Accuracy**: The proxy compares our local shims (Weather, VOACAP, etc.) against the original backend.
- **Reliability**: If our local shim fails or is missing data, the proxy **automatically falls back** to the original backend, ensuring your clock never "breaks."

## Monitoring Parity

You can see how well our local shims are matching the "real world" by visiting the Parity Dashboard:

**URL**: `http://<your-server-ip>:9086/parity`

## Reporting Discrepancies

Check `logs/parity_summary.json` or the dashboard. If you see persistent "Diff" status for endpoints you care about, please share your `logs/proxy.log` with the development team!

## Project Layout
- `server.py`: The local backend shimming service.
- `shadow_proxy/`: The intelligent monitoring layer.
- `ingestion/`: Background fetchers that keep data fresh.
- `logs/`: Diagnostic output for community debugging.
