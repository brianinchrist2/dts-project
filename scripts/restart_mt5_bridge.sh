#!/bin/bash
# Restart MT5 Bridge

echo "Restarting MT5 Bridge..."

# Kill existing mt5linux processes
docker exec mt5_service pkill -f "mt5linux" || true

# Wait a bit
sleep 2

# Start mt5linux in Wine
docker exec -u abc mt5_service wine "/config/.wine/drive_c/Program Files (x86)/Python39-32/python.exe" -m mt5linux --host 0.0.0.0 -p 8001 &

# Wait for startup
sleep 5

# Verify port is listening
if docker exec mt5_service ss -tlnp | grep ":8001" > /dev/null; then
    echo "MT5 Bridge is running on port 8001"
else
    echo "Failed to start MT5 Bridge"
    exit 1
fi
