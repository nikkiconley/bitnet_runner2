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

(Optional) Test inference.

```shell
python run_inference.py -m models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf -p "What is the capital of the USA?" -t 4 -n 100
```

### Setup bitnet_runner2

Clone the project.

```shell
cd ~
git clone https://github.com/dkirby-ms/bitnet_runner2
conda deactivate
python -m venv .venv
source .venv/bin/activate
```

Install packages.

```shell
pip install -r requirements.txt
```

## Usage

### Service Commands

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

