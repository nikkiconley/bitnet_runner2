# BitNet MQTT Device with Certificate Management

A Python application that creates an intelligent IoT device using BitNet inference and MQTT messaging, with automatic device registration and certificate management through the Makerspace Certificate Service.

## Features

- **Automatic Device Registration**: Integrates with the Makerspace Certificate Service for seamless device registration
- **Certificate Management**: Automatically handles device certificates for secure MQTT communication
- **BitNet Integration**: Uses BitNet inference to generate intelligent responses to messages
- **MQTT Communication**: Subscribe and publish to MQTT topics for device-to-device communication
- **Azure Event Grid Support**: Configured for Azure Event Grid MQTT broker with TLS authentication
- **Smart Response Logic**: Configurable criteria for when to respond to messages
- **Context Awareness**: Maintains conversation context for better responses
- **Background Service**: Runs as a service on Raspberry Pi devices

## Architecture

```
Pi Device ←→ Azure Event Grid MQTT ←→ Other Devices
     ↓              ↓                      ↓
Certificate    Certificate           Certificate
  Service       Validation            Service
     ↓              ↓                      ↓
  BitNet        Message               BitNet
 Inference      Routing              Inference
```

## Prerequisites

- Python 3.8 or higher
- BitNet repository cloned and built
- Internet connection for certificate service
- Raspberry Pi or compatible Linux device

## Quick Start

1. **Install the service:**
   ```bash
   ./install.sh
   ```

2. **Configure your device:**
   Edit `config.json` to set your device details:
   ```json
   {
     "device_type": "raspberry_pi",
     "location": "makerspace_lab_1",
     "description": "3D printer monitoring device",
     "bitnet_path": "/path/to/BitNet"
   }
   ```

3. **Register your device:**
   ```bash
   python3 bitnet_mqtt_device.py --config config.json register
   ```

4. **Test BitNet inference:**
   ```bash
   python3 bitnet_mqtt_device.py --config config.json test "Hello world"
   ```

5. **Start the service:**
   ```bash
   ./start_service.sh
   ```

## Configuration

The service uses a JSON configuration file. Key sections:

### MQTT Settings
```json
{
  "mqtt": {
    "broker": "makerspace-eventgrid.westus2-1.ts.eventgrid.azure.net",
    "port": 8883,
    "topic": "devices/bitnet/messages",
    "use_tls": true
  }
}
```

### Device Registration
```json
{
  "cert_service_url": "https://makerspace-cert-service.proudwave-5e4592e9.westus2.azurecontainerapps.io",
  "device_type": "raspberry_pi",
  "location": "makerspace",
  "capabilities": ["mqtt", "bitnet", "ai_inference"]
}
```

### Response Criteria
```json
{
  "response_criteria": {
    "default_respond": true,
    "probability": 0.8,
    "message_types": ["general", "question"],
    "content_filters": ["help", "what", "how", "explain", "?"]
  }
}
```

## Usage

### Service Commands

**Run as service:**
```bash
python3 bitnet_mqtt_device.py --config config.json service
```

**Send manual message:**
```bash
python3 bitnet_mqtt_device.py --config config.json send "Hello network!"
./send_message.sh "How do I use a 3D printer?"
```

**Test inference:**
```bash
python3 bitnet_mqtt_device.py --config config.json test "What is IoT?"
```

**Validate setup:**
```bash
python3 bitnet_mqtt_device.py --config config.json validate
```

**Register device:**
```bash
python3 bitnet_mqtt_device.py --config config.json register
```

## Message Format

Messages are JSON objects with this structure:

```json
{
  "id": "unique-message-id",
  "device_id": "bitnet-hostname-abc123",
  "content": "How do I calibrate my 3D printer?",
  "timestamp": "2025-06-23T10:30:00",
  "message_type": "question"
}
```

### Message Types

- **general**: Normal conversation messages
- **question**: Direct questions
- **response**: Responses to other messages
- **presence**: Device join/leave notifications
- **manual**: Manually sent messages

## Certificate Management

The service automatically:

1. **Registers** the device with the certificate service
2. **Retrieves** device-specific certificates
3. **Validates** certificate expiration
4. **Renews** certificates when needed
5. **Configures** MQTT TLS authentication

Certificates are stored in the `./certs/` directory:
- `{device_id}.crt` - Client certificate
- `{device_id}.key` - Private key
- `ca.crt` - CA certificate

## BitNet Integration

The service integrates with BitNet for AI inference:

### Configuration
```json
{
  "bitnet_path": "../BitNet",
  "bitnet_params": {
    "n_predict": 128,
    "threads": 2,
    "ctx_size": 2048,
    "temperature": 0.8
  }
}
```

### Custom Prompts
```json
{
  "prompt_template": "You are a helpful AI assistant in a makerspace IoT network. Device {device_id} said: '{content}'. Recent context: {context}. Provide a helpful, concise response about making, building, or technology."
}
```

## Troubleshooting

**Service won't start:**
- Check BitNet setup: `python3 bitnet_mqtt_device.py --config config.json validate`
- Verify network connectivity to certificate service
- Check log file for error details

**Certificate issues:**
- Re-register device: `python3 bitnet_mqtt_device.py --config config.json register`
- Check certificate service URL in config
- Verify device has internet access

**MQTT connection issues:**
- Verify Azure Event Grid broker settings
- Check firewall settings for port 8883
- Validate certificates with validate command

**No responses generated:**
- Test inference: `python3 bitnet_mqtt_device.py --config config.json test "hello"`
- Check response criteria configuration
- Monitor logs for generation attempts

## Files Structure

```
bitnet_runner2/
├── bitnet_mqtt_device.py      # Main service application
├── config.json                # Service configuration
├── requirements.txt           # Python dependencies
├── install.sh                 # Installation script
├── start_service.sh          # Service startup script
├── send_message.sh           # Send test messages
├── certs/                    # Certificate storage
│   ├── {device_id}.crt      # Client certificate
│   ├── {device_id}.key      # Private key
│   └── ca.crt               # CA certificate
└── README.md                 # This documentation
```

## Integration with Makerspace

This device is designed to work with the Makerspace 2025 ecosystem:

- **Certificate Service**: Automatic device registration and certificate management
- **Azure Event Grid**: Secure MQTT communication
- **BitNet AI**: Intelligent responses for makerspace questions
- **IoT Network**: Participates in distributed makerspace intelligence

Example use cases:
- Equipment status monitoring and responses
- Educational assistance for makers
- Collaborative project coordination
- Safety and procedural guidance
