# BitNet MQTT Device Setup Guide

This guide will help you set up a Raspberry Pi device that subscribes to MQTT topics and uses BitNet for AI-powered responses, with automatic certificate management through the Makerspace Certificate Service.

## System Requirements

- Raspberry Pi 4 or newer (recommended)
- Raspberry Pi OS (Debian-based)
- Python 3.8 or higher
- 4GB+ RAM (for BitNet inference)
- Internet connection
- 16GB+ SD card

## Pre-Installation Steps

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Required System Packages
```bash
sudo apt install -y python3-pip python3-venv git build-essential cmake
```

### 3. Install BitNet (if not already installed)
```bash
# Clone BitNet repository
git clone --recursive https://github.com/microsoft/BitNet.git
cd BitNet

# Install dependencies
pip3 install -r requirements.txt

# Build BitNet (this may take a while)
python setup_env.py -md models/BitNet-b1.58-2B-4T -q i2_s
```

## Installation

### 1. Clone and Setup the BitNet MQTT Device
```bash
# Clone or copy the BitNet MQTT Device files
git clone <your-repo> bitnet_runner2
# Or manually create the directory and copy files

cd bitnet_runner2

# Run the installation script
./install.sh
```

### 2. Configure the Device
Edit the `config.json` file to match your setup:

```json
{
  "mqtt": {
    "broker": "makerspace-eventgrid.westus2-1.ts.eventgrid.azure.net",
    "port": 8883,
    "topic": "devices/bitnet/messages"
  },
  "bitnet_path": "/path/to/BitNet",
  "device_type": "raspberry_pi",
  "location": "your_location",
  "description": "Your device description"
}
```

### 3. Register the Device
```bash
python3 bitnet_mqtt_device.py --config config.json register
```

### 4. Validate Setup
```bash
python3 bitnet_mqtt_device.py --config config.json validate
```

## Running the Service

### Manual Start
```bash
# Start the service manually
./start_service.sh

# Or directly with Python
python3 bitnet_mqtt_device.py --config config.json service
```

### Systemd Service (Recommended)
```bash
# Install as systemd service
sudo ./install_systemd.sh

# Start the service
sudo systemctl start bitnet-mqtt-device

# Enable auto-start on boot
sudo systemctl enable bitnet-mqtt-device

# Check status
sudo systemctl status bitnet-mqtt-device

# View logs
sudo journalctl -u bitnet-mqtt-device -f
```

## Testing

### 1. Test BitNet Inference
```bash
python3 bitnet_mqtt_device.py --config config.json test "Hello, how can I help you?"
```

### 2. Send Test Message
```bash
./send_message.sh "What is 3D printing?"
```

### 3. Monitor Logs
```bash
tail -f bitnet_mqtt_device.log
```

## Network Configuration

### MQTT Topic Structure
- **Main Topic**: `devices/bitnet/messages`
- **Message Format**: JSON with device_id, content, timestamp, message_type

### Message Types
- `general` - Normal conversation
- `question` - Direct questions
- `response` - AI responses
- `presence` - Device status
- `manual` - Manual messages

### Example Message
```json
{
  "id": "uuid-here",
  "device_id": "bitnet-raspberrypi-abc123",
  "content": "How do I calibrate my 3D printer?",
  "timestamp": "2025-06-23T10:30:00",
  "message_type": "question"
}
```

## Troubleshooting

### Common Issues

**1. Certificate Service Connection Failed**
```bash
# Check internet connection
ping makerspace-cert-service.proudwave-5e4592e9.westus2.azurecontainerapps.io

# Re-register device
python3 bitnet_mqtt_device.py --config config.json register
```

**2. BitNet Inference Fails**
```bash
# Check BitNet setup
python3 bitnet_mqtt_device.py --config config.json validate

# Verify BitNet path in config.json
# Ensure BitNet is properly built
```

**3. MQTT Connection Issues**
```bash
# Check certificates
ls -la certs/

# Validate certificates
python3 bitnet_mqtt_device.py --config config.json validate

# Check Azure Event Grid settings
```

**4. Service Won't Start**
```bash
# Check logs
tail -f bitnet_mqtt_device.log

# Check systemd status
sudo systemctl status bitnet-mqtt-device

# View systemd logs
sudo journalctl -u bitnet-mqtt-device -n 50
```

### Log Files
- `bitnet_mqtt_device.log` - Application logs
- `sudo journalctl -u bitnet-mqtt-device` - Systemd logs

### Performance Tuning

**For Raspberry Pi 4 (4GB RAM):**
```json
{
  "bitnet_params": {
    "threads": 2,
    "n_predict": 64,
    "ctx_size": 1024
  }
}
```

**For Raspberry Pi 4 (8GB RAM):**
```json
{
  "bitnet_params": {
    "threads": 4,
    "n_predict": 128,
    "ctx_size": 2048
  }
}
```

## Security Considerations

1. **Certificates**: Automatically managed and renewed
2. **TLS**: All MQTT communication encrypted
3. **Private Keys**: Stored with secure permissions (600)
4. **Device Authentication**: Unique device certificates

## Monitoring

### Health Checks
```bash
# Check service status
sudo systemctl is-active bitnet-mqtt-device

# View recent logs
sudo journalctl -u bitnet-mqtt-device --since "1 hour ago"

# Monitor resource usage
htop
```

### Metrics to Monitor
- CPU usage during inference
- Memory usage
- Network connectivity
- Certificate expiration
- MQTT connection status

## Integration with Makerspace

This device integrates with:
- **Certificate Service**: Automatic device registration
- **Azure Event Grid**: Secure MQTT messaging
- **BitNet AI**: Intelligent response generation
- **Makerspace Network**: Collaborative IoT ecosystem

The device can be used for:
- Equipment monitoring and assistance
- Educational Q&A for makers
- Project collaboration
- Safety and procedural guidance
- Real-time help and support

## Updates and Maintenance

### Updating the Service
```bash
# Stop the service
sudo systemctl stop bitnet-mqtt-device

# Update code (pull from git or copy new files)
git pull

# Restart the service
sudo systemctl start bitnet-mqtt-device
```

### Certificate Renewal
Certificates are automatically renewed when they approach expiration. Manual renewal:
```bash
python3 bitnet_mqtt_device.py --config config.json register
```

### Log Rotation
Consider setting up log rotation for the application logs:
```bash
sudo nano /etc/logrotate.d/bitnet-mqtt-device
```

Add:
```
/home/pi/bitnet_runner2/bitnet_mqtt_device.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
```
