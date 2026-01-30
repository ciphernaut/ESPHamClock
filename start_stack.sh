#!/bin/bash
# start_stack.sh

echo "Starting HamClock stack at $(date)" > start_debug.log

# Port Cleanup
fuser -k 8081/tcp 9085/tcp 9086/tcp >> start_debug.log 2>&1
sleep 2

# Start Backend
python3 -u server.py > server_final_v2.log 2>&1 &
echo "Server started (PID $!)" >> start_debug.log

# Start Proxy
python3 -u shadow_proxy/proxy.py > proxy_final_v2.log 2>&1 &
echo "Proxy started (PID $!)" >> start_debug.log

sleep 3

# Start Client
./hamclock-web-800x480 > hamclock_final_v2.log 2>&1 &
echo "Client started (PID $!)" >> start_debug.log

echo "Stack initialization complete." >> start_debug.log
