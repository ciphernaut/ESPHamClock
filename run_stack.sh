#!/bin/bash

# HamClock Stack Manager
# Supports start, stop, restart, and status for specific components or 'all'.
# Usage: ./run_stack.sh [command] [component]
# Commands: start, stop, restart, status (default: status)
# Components: backend, proxy, client, all (default: all)

LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

# Ports
PROXY_PORT=9085
BACKEND_PORT=9086
UI_PORT=8081

COMMAND=${1:-"status"}
COMPONENT=${2:-"all"}

echo "--- ESPHamClock Service Manager: $COMMAND $COMPONENT ---"

check_port() {
    local port=$1
    local name=$2
    if ss -tulpn | grep -q ":$port "; then
        echo "[OK] $name is running on port $port"
        return 0
    else
        echo "[OFF] $name is NOT running on port $port"
        return 1
    fi
}

status_backend() {
    check_port $BACKEND_PORT "Backend (server.py)"
    # Also check scheduler process
    if pgrep -f "python3 ingestion/scheduler.py" > /dev/null; then
        echo "[OK] Scheduler (ingestion/scheduler.py) is running"
    else
        echo "[OFF] Scheduler (ingestion/scheduler.py) is NOT running"
    fi
}

status_proxy() {
    check_port $PROXY_PORT "Shadow Proxy"
}

status_client() {
    check_port $UI_PORT "Local Client"
}

stop_backend() {
    echo "Stopping Backend (Port $BACKEND_PORT) and Scheduler..."
    fuser -k "$BACKEND_PORT/tcp" 2>/dev/null
    pkill -f "python3 ingestion/scheduler.py" 2>/dev/null
    sleep 1
}

stop_proxy() {
    echo "Stopping Proxy (Port $PROXY_PORT)..."
    fuser -k "$PROXY_PORT/tcp" 2>/dev/null
    sleep 1
}

stop_client() {
    echo "Stopping Local Client (Port $UI_PORT)..."
    fuser -k "$UI_PORT/tcp" 2>/dev/null
    sleep 1
}

start_backend() {
    stop_backend
    echo "Starting Backend Server (Port $BACKEND_PORT)..."
    python3 -u server.py >> "$LOG_DIR/server.log" 2>&1 &
    echo "Starting Data Scheduler..."
    python3 -u ingestion/scheduler.py >> "$LOG_DIR/scheduler.log" 2>&1 &
}

start_proxy() {
    stop_proxy
    echo "Starting Shadow Proxy (Port $PROXY_PORT) in SHADOW mode..."
    export PROXY_MODE=SHADOW
    python3 -u shadow_proxy/proxy.py >> "$LOG_DIR/proxy.log" 2>&1 &
}

start_client() {
    if [ -f "./hamclock-web-800x480" ]; then
        stop_client
        echo "Starting Local HamClock Client (Port $UI_PORT)..."
        ./hamclock-web-800x480 >> "$LOG_DIR/hamclock.log" 2>&1 &
    else
        echo "No local client (./hamclock-web-800x480) found. Skipping."
    fi
}

case "$COMMAND" in
    start|restart)
        case "$COMPONENT" in
            backend) start_backend ;;
            proxy)   start_proxy ;;
            client)  start_client ;;
            all)     start_backend; start_proxy; start_client ;;
            *) echo "Unknown component: $COMPONENT"; exit 1 ;;
        esac
        ;;
    stop)
        case "$COMPONENT" in
            backend) stop_backend ;;
            proxy)   stop_proxy ;;
            client)  stop_client ;;
            all)     stop_backend; stop_proxy; stop_client ;;
            *) echo "Unknown component: $COMPONENT"; exit 1 ;;
        esac
        ;;
    status)
        case "$COMPONENT" in
            backend) status_backend ;;
            proxy)   status_proxy ;;
            client)  status_client ;;
            all)     status_backend; status_proxy; status_client ;;
            *) echo "Unknown component: $COMPONENT"; exit 1 ;;
        esac
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|status] [backend|proxy|client|all]"
        exit 1
        ;;
esac

echo "Done. Logs available in $LOG_DIR"
