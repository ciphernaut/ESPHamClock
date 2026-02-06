#!/bin/bash

# HamClock Stack Manager
# Supports start, stop, restart, and status for specific components or 'all'.
# Usage: ./run_stack.sh [command] [component]
# Commands: start, stop, restart, status (default: status)
# Components: backend, proxy, client, all (default: all)

LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

# Ports and Configuration
BACKEND_PORT=9086

# Proxy 1 (Shadow)
SHADOW_PROXY_PORT=9085
# Proxy 2 (Verify)
VERIFY_PROXY_PORT=9095

# Client 1 (DUT)
CLIENT1_NAME="ax4test"
CLIENT1_DIR="$HOME/.hamclock/$CLIENT1_NAME"
CLIENT1_RO=8081
CLIENT1_RW=8091
CLIENT1_REST=8001

# Client 2 (original)
CLIENT2_NAME="ax4upstream"
CLIENT2_DIR="$HOME/.hamclock/$CLIENT2_NAME"
CLIENT2_RO=8082
CLIENT2_RW=8092
CLIENT2_REST=8002

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
    if pgrep -f "backend/ingestion/scheduler.py" > /dev/null; then
        echo "[OK] Scheduler (backend/ingestion/scheduler.py) is running"
    else
        echo "[OFF] Scheduler (backend/ingestion/scheduler.py) is NOT running"
    fi
}

status_proxy() {
    check_port $SHADOW_PROXY_PORT "Shadow Proxy (VK4SHF)"
    check_port $VERIFY_PROXY_PORT "Verify Proxy (VK4SGE)"
}

status_client() {
    check_port $CLIENT1_RW "Client VK4SHF (RW)"
    check_port $CLIENT2_RW "Client VK4SGE (RW)"
}

stop_backend() {
    echo "Stopping Backend (Port $BACKEND_PORT) and Scheduler..."
    pkill -f "python3 -u backend/server.py" 2>/dev/null
    pkill -f "python3 -u backend/ingestion/scheduler.py" 2>/dev/null
    sleep 1
}

stop_proxy() {
    echo "Stopping Proxies..."
    pkill -f "python3 -u proxy/proxy.py" 2>/dev/null
    sleep 1
}

stop_client() {
    echo "Stopping Clients..."
    pkill -f "hamclock-web-1600x960" 2>/dev/null
    sleep 1
}

start_backend() {
    stop_backend
    echo "Starting Backend Server (Port $BACKEND_PORT)..."
    python3 -u backend/server.py >> "$LOG_DIR/server.log" 2>&1 &
    echo "Starting Data Scheduler..."
    python3 -u backend/ingestion/scheduler.py >> "$LOG_DIR/scheduler.log" 2>&1 &
}

start_proxy() {
    stop_proxy
    echo "Starting Shadow Proxy (Port $SHADOW_PROXY_PORT)..."
    export PROXY_MODE=SHADOW
    export PROXY_PORT=$SHADOW_PROXY_PORT
    python3 -u proxy/proxy.py >> "$LOG_DIR/proxy_shadow.log" 2>&1 &
    
    echo "Starting Verify Proxy (Port $VERIFY_PROXY_PORT)..."
    export PROXY_MODE=VERIFY
    export PROXY_PORT=$VERIFY_PROXY_PORT
    python3 -u proxy/proxy.py >> "$LOG_DIR/proxy_verify.log" 2>&1 &
}

start_client() {
    local client_bin="./bin/hamclock-web-1600x960"
    if [ -f "$client_bin" ]; then
        stop_client
        echo "Starting Client $CLIENT1_NAME (RW:$CLIENT1_RW)..."
        mkdir -p "$CLIENT1_DIR"
        "$client_bin" -k -d "$CLIENT1_DIR" -b "localhost:$SHADOW_PROXY_PORT" -r "$CLIENT1_RO" -w "$CLIENT1_RW" -e "$CLIENT1_REST" >> "$LOG_DIR/hamclock_$CLIENT1_NAME.log" 2>&1 &
        
        echo "Starting Client $CLIENT2_NAME (RW:$CLIENT2_RW)..."
        mkdir -p "$CLIENT2_DIR"
        "$client_bin" -k -d "$CLIENT2_DIR" -b "localhost:$VERIFY_PROXY_PORT" -r "$CLIENT2_RO" -w "$CLIENT2_RW" -e "$CLIENT2_REST" >> "$LOG_DIR/hamclock_$CLIENT2_NAME.log" 2>&1 &
        
        # Give them a moment to start before setup
        echo "Waiting for clients to initialize..."
        sleep 5
        setup_clients
    else
        echo "No local client ($client_bin) found. Skipping."
    fi
}

setup_clients() {
    echo "Performing initial setup for clients via REST API..."
    # Client 1: VK4SHF
    echo "Setting up $CLIENT1_NAME on port $CLIENT1_REST..."
    curl -s "http://localhost:$CLIENT1_REST/set_newde?call=$CLIENT1_NAME" > /dev/null
    # Client 2: VK4SGE
    echo "Setting up $CLIENT2_NAME on port $CLIENT2_REST..."
    curl -s "http://localhost:$CLIENT2_REST/set_newde?call=$CLIENT2_NAME" > /dev/null
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
