#!/bin/bash

# Start the BitNet MQTT Device service

CONFIG_FILE="config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    echo "Run ./install.sh first"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting BitNet MQTT Device Service..."
python3 bitnet_mqtt_device.py --config "$CONFIG_FILE" service
