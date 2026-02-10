# Parity Debugging Skill
This skill provides tools and workflows for efficiently debugging parity between HamClock instances.

## Overview
The skill focuses on semantic comparison of REST API endpoints and automated state synchronization between a test instance (`ax4test`) and a baseline instance (`ax4upstream`).

## Components
- `scripts/compare_endpoint.py`: Performs semantic diffing of REST responses.
- `scripts/init_clients.py`: Synchronizes the state (callsign, location, etc.) of multiple instances.

## Workflows

### 1. Initialize Test Environment
Use this workflow to ensure both clients are in the same state before running tests.
```bash
python3 skills/parity_debug/scripts/init_clients.py --call ax4test --lat -26 --lng 153
```

### 2. Verify Endpoint Parity
Compare a specific endpoint between the two clients.
```bash
python3 skills/parity_debug/scripts/compare_endpoint.py http://localhost:8001/get_spacewx.txt http://localhost:8002/get_spacewx.txt get_spacewx.txt
```

### 3. Run Full Parity Sweep
Run a batch comparison across all configured common endpoints.
```bash
python3 skills/parity_debug/scripts/batch_compare.py
```

## Guidelines for Agents
- ALWAYS use `compare_endpoint.py` for regression testing after changing backend logic.
- If a discrepancy is found, check if it's "noise" (like a timestamp) and update `clean_response` in `compare_endpoint.py` to filter it semantically.
