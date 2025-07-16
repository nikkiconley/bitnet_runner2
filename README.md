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
.miniconda/bin/conda init
```

Restart your shell to complete the miniconda setup.

### Setup BitNet

#### Requirements
- python>=3.9
- cmake>=3.22
- clang>=18
    - For Windows users, install [Visual Studio 2022](https://visualstudio.microsoft.com/downloads/). In the installer, toggle on at least the following options(this also automatically installs the required additional tools like CMake):
        -  Desktop-development with C++
        -  C++-CMake Tools for Windows
        -  Git for Windows
        -  C++-Clang Compiler for Windows
        -  MS-Build Support for LLVM-Toolset (clang)
    - For Debian/Ubuntu users, you can download with [Automatic installation script](https://apt.llvm.org/)

        `bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)"`
- conda (highly recommend)

#### Get the BitNet code.

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

