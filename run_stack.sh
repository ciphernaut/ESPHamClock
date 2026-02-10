#!/bin/bash

# HamClock Stack Manager
# Standardized logging to ./logs/

LOG_DIR="./logs"
mkdir -p $LOG_DIR

# Ports
# Ports
UI_PORT=8081
PROXY_PORT=9085
BACKEND_PORT=9086

echo "Stopping existing processes..."
fuser -k $UI_PORT/tcp $PROXY_PORT/tcp $BACKEND_PORT/tcp 2>/dev/null
sleep 2

echo "Starting Backend Server (Port $BACKEND_PORT)..."
python3 -u server.py >> $LOG_DIR/server.log 2>&1 &

echo "Starting Shadow Proxy (Port $PROXY_PORT) in SHADOW mode..."
export PROXY_MODE=SHADOW
python3 -u shadow_proxy/proxy.py >> $LOG_DIR/proxy.log 2>&1 &

echo "Starting HamClock Client (UI Port $UI_PORT) via Proxy: $PROXY_PORT"
./hamclock-web-800x480 >> $LOG_DIR/hamclock.log 2>&1 &

echo "Stack started in SHADOW mode for community testing."
echo "Logs available in $LOG_DIR:"
echo "  - Backend: $LOG_DIR/server.log"
echo "  - Proxy:   $LOG_DIR/proxy.log"
echo "  - Client:  $LOG_DIR/hamclock.log"
echo "  - Diffs:   ./discrepancies.log"
