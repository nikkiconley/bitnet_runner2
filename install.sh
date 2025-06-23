#!/bin/bash

# Installation script for BitNet MQTT Device with Certificate Management

set -e

echo "Installing BitNet MQTT Device..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as normal user."
   exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create certificates directory
mkdir -p certs

# Make scripts executable
chmod +x bitnet_mqtt_device.py
chmod +x install.sh

echo "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config.json to configure your device settings"
echo "2. Ensure BitNet is installed and configured at the specified path"
echo "3. Register your device: python3 bitnet_mqtt_device.py --config config.json register"
echo "4. Test the service: python3 bitnet_mqtt_device.py --config config.json test 'Hello world'"
echo "5. Start the service: python3 bitnet_mqtt_device.py --config config.json service"
echo ""
echo "For Azure Event Grid MQTT:"
echo "- The service will automatically register with the certificate service"
echo "- Certificates will be managed automatically"
echo "- Default topic: devices/bitnet/messages"
