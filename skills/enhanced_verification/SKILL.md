# Enhanced Verification Skill
This skill provides advanced tools for verifying HamClock parity through state injection, visual comparison, and log analysis.

## Overview
Allows complex end-to-end testing by driving the client via REST API (`set_` commands), waiting for stabilization, and verifying state via:
1.  **State Snapshots**: Comparing `get_config` and other endpoints.
2.  **Visual Verification**: Diffing screen captures.
3.  **Log Analysis**: Correlating steps with backend/proxy logs.

## Components
- `scripts/client_driver.py`: Wrapper for REST API interactions with retry/settle logic.
- `scripts/visual_verifier.py`: Compares images from `get_capture.bmp`.
### 3. Log Monitor (`scripts/log_monitor.py`)
Tails and analyzes diagnostic logs for specific events or errors.
- `wait_for_pattern(pattern, timeout)`: Blocking wait for a log entry.

### 4. Orchestrator (`scripts/verify_parity_complex.py`)
Example script demonstrating a complex parity test (e.g., VOACAP scenario).
- Uses `client_driver` to set state.
- Uses `visual_verifier` to compare screenshots.
- Uses `log_monitor` to check for errors (optional).

## Workflows

### 1. Complex Parity Test
Execute a scenario that sets specific state (e.g. VOACAP on Pane 1) and verifies it matches the baseline.
```bash
python3 skills/enhanced_verification/scripts/verify_parity_complex.py --scenario voacap_pane1
```

## Guidelines for Agents
- **Wait for Settle**: Always use the driver's wait methods after setting state. Client is asynchronous.
- **Prefer WebServer API**: Use `set_pane`, `set_voacap` etc. over `set_touch` for deterministic tests.
- **Visuals are Logic**: Use visual diffs to catch rendering bugs that data endpoints miss (e.g. text overlap).
