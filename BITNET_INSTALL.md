# Bitnet setup

## Setup guide (Debian/ARM)

### Setup miniconda

mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh

### Setup BitNet

git clone --recursive https://github.com/microsoft/BitNet.git
cd BitNet

conda create -n bitnet-cpp python=3.9
conda activate bitnet-cpp

pip install -r requirements.txt

### Manually download the model and run with local path

huggingface-cli download microsoft/BitNet-b1.58-2B-4T-gguf --local-dir models/BitNet-b1.58-2B-4T
python setup_env.py -md models/BitNet-b1.58-2B-4T -q i2_s
