#!/bin/bash

# Test script to send a message to the MQTT topic

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

if [ -z "$1" ]; then
    echo "Usage: $0 <message>"
    echo "Example: $0 'Hello, can you help me with 3D printing?'"
    exit 1
fi

echo "Sending test message: $1"
python3 bitnet_mqtt_device.py --config "$CONFIG_FILE" send "$1"
