# BitNet MQTT Device with Certificate Management

A Python application that creates an intelligent IoT device using BitNet inference and MQTT messaging. Designed to work with the [Makerspace Certificate Service](https://github.com/dkirby-ms/makerspace2025).

## Setup guide (Debian/ARM)

### Install dependencies

```shell
sudo apt install clang
```

### Setup miniconda

```shell
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
./bin/conda init
```

Restart your shell to complete the miniconda setup.

### Setup BitNet

Get the BitNet code.

```shell
git clone --recursive https://github.com/microsoft/BitNet.git
cd BitNet
```

Setup a conda environment for BitNet.

```shell
conda create -n bitnet-cpp python=3.9
conda activate bitnet-cpp
pip install -r requirements.txt
```

Get the model and setup for local inference.

```shell
huggingface-cli download microsoft/BitNet-b1.58-2B-4T-gguf --local-dir models/BitNet-b1.58-2B-4T
python setup_env.py -md models/BitNet-b1.58-2B-4T -q i2_s
```

### Setup bitnet_runner2



```shell
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

