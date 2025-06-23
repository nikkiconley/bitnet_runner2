#!/bin/bash

# Install BitNet MQTT Device as systemd service

set -e

SERVICE_NAME="bitnet-mqtt-device"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOCAL_SERVICE_FILE="bitnet-mqtt-device.service"

echo "Installing BitNet MQTT Device as systemd service..."

# Check if running with sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run with sudo for systemd installation"
   echo "Usage: sudo ./install_systemd.sh"
   exit 1
fi

# Check if service file exists locally
if [ ! -f "$LOCAL_SERVICE_FILE" ]; then
    echo "Service file not found: $LOCAL_SERVICE_FILE"
    exit 1
fi

# Get the actual user who called sudo
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

# Create a customized service file with correct paths
echo "Creating systemd service file..."
sed "s|/home/pi/bitnet_runner2|$PWD|g; s|User=pi|User=$ACTUAL_USER|g; s|Group=pi|Group=$ACTUAL_USER|g" "$LOCAL_SERVICE_FILE" > "$SERVICE_FILE"

# Reload systemd
systemctl daemon-reload

# Enable the service
systemctl enable "$SERVICE_NAME"

echo "Service installed successfully!"
echo ""
echo "Usage:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo "  Disable: sudo systemctl disable $SERVICE_NAME"
