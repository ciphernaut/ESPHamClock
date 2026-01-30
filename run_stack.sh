#!/bin/bash

# HamClock Stack Manager
# Standardized logging to ./logs/

LOG_DIR="./logs"
mkdir -p $LOG_DIR

# Ports (Backend Services)
PROXY_PORT=9085
BACKEND_PORT=9086
UI_PORT=8081      # Local Web UI (Optional)

echo "--- ESPHamClock Backend Services ---"

# 1. STOP EXISTING SERVICES
echo "Stopping existing backend services..."
fuser -k $PROXY_PORT/tcp $BACKEND_PORT/tcp 2>/dev/null
pkill -f "python3 ingestion/scheduler.py" 2>/dev/null
sleep 2

# 2. START BACKEND GROUP
echo "Starting Backend Server (Port $BACKEND_PORT)..."
python3 -u server.py >> $LOG_DIR/server.log 2>&1 &
BACKEND_PID=$!

echo "Starting Data Scheduler (Background)..."
python3 -u ingestion/scheduler.py >> $LOG_DIR/scheduler.log 2>&1 &
SCHEDULER_PID=$!

echo "Starting Shadow Proxy (Port $PROXY_PORT) in SHADOW mode..."
export PROXY_MODE=SHADOW
python3 -u shadow_proxy/proxy.py >> $LOG_DIR/proxy.log 2>&1 &
PROXY_PID=$!

echo "Backend Services Group Started (PIDs: $BACKEND_PID, $SCHEDULER_PID, $PROXY_PID)"

# 3. OPTIONAL LOCAL CLIENT
if [ -f "./hamclock-web-800x480" ]; then
    echo "Starting Local HamClock Client (UI Port $UI_PORT)..."
    fuser -k $UI_PORT/tcp 2>/dev/null
    ./hamclock-web-800x480 >> $LOG_DIR/hamclock.log 2>&1 &
    CLIENT_PID=$!
    echo "Local Client Started (PID: $CLIENT_PID)"
else
    echo "No local client found. Services are ready for remote ESP devices on Port $PROXY_PORT."
fi

echo "Detailed logs available in $LOG_DIR"
