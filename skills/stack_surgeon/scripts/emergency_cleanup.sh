#!/bin/bash

# emergency_cleanup.sh - Forcefully clean up HamClock-related processes and resources.

echo "--- Stack Surgeon: Emergency Cleanup Initiated ---"

# 1. Force kill all related processes
echo "Forcefully terminating processes..."
PROCESS_PATTERNS=("hamclock-web" "proxy/proxy.py" "backend/server.py" "backend/ingestion/scheduler.py" "run_stack.sh")

for PATTERN in "${PROCESS_PATTERNS[@]}"; do
    echo "  Killing matches for: $PATTERN"
    pkill -9 -f "$PATTERN" 2>/dev/null
done

# 2. Clear known ports using fuser (as backup)
echo "Clearing ports..."
PORTS=(9085 9095 9086 8081 8091 8001 8082 8092 8002)
for PORT in "${PORTS[@]}"; do
    echo "  Releasing port: $PORT"
    fuser -k "$PORT/tcp" 2>/dev/null
done

# 3. Cleanup stale logs if they are too large (optional safety check)
# DISCREPANCY_LOG="logs/discrepancies.log"
# if [ -f "$DISCREPANCY_LOG" ] && [ $(stat -c%s "$DISCREPANCY_LOG") -gt 100000000 ]; then
#     echo "  Rotating massive discrepancy log..."
#     mv "$DISCREPANCY_LOG" "${DISCREPANCY_LOG}.old"
# fi

# 4. Final check
echo "Final process check:"
ps -ef | grep -E "hamclock|proxy|backend" | grep -v grep || echo "  Clean."

echo "--- Cleanup Complete. System should be responsive. ---"
