# AI Agent Guide: Service Management & Debugging

This document is for AI agents (like Antigravity) to ensure consistent service management and prevent "context rot."

## Service Architecture

| Component | Service(s) | Port | Log File |
| :--- | :--- | :--- | :--- |
| **Backend** | `server.py`, `ingestion/scheduler.py` | 9086 | `logs/server.log`, `logs/scheduler.log` |
| **Proxy** | `shadow_proxy/proxy.py` | 9085 | `logs/proxy.log` |
| **Client** | `./hamclock-web-800x480` (Binary) | 8081 | `logs/hamclock.log` |

## How to Manage Services

Use the improved `./run_stack.sh` script. **Do not use `fuser` or `pkill` manually unless necessary.**

### Common Commands

*   **Check status of all services:**
    ```bash
    ./run_stack.sh status all
    ```
*   **Restart everything (Standard debug step):**
    ```bash
    ./run_stack.sh restart all
    ```
*   **Restart only the backend (If you changed `server.py` or ingestion logic):**
    ```bash
    ./run_stack.sh restart backend
    ```
*   **Stop everything:**
    ```bash
    ./run_stack.sh stop all
    ```

### Usage Pattern
Always prefer the grouped commands:
`./run_stack.sh [start|stop|restart|status] [backend|proxy|client|all]`

## Debugging Workflow

1.  **Make changes** to the code.
2.  **Restart the relevant component** using `./run_stack.sh restart <component>`.
3.  **Check logs** immediately: `tail -f logs/<relevant>.log`.
4.  **Verify parity** if working on the proxy: visit `http://localhost:9085/parity` (if reachable) or check `logs/proxy.log`.

## Important Files
- `server.py`: Main backend entry point.
- `shadow_proxy/proxy.py`: Intelligent proxy layer.
- `ingestion/scheduler.py`: Runs background data fetchers.
- `run_stack.sh`: The source of truth for service management.
