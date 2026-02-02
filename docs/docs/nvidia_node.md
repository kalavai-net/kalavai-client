---
tags:
  - nvidia
  - cuda
---

# Pre-requisites

Kalavai platform supports the use of both NVIDIA and AMD cards. To ensure full compatibility, the worker node must have the following requirements met:

- OS: Linux
- Python: 3.12+
- GPU: Any modern architecture after Pascal (2016) should work (Pascal, Volta, Turing, Ampere, Hopper, Ada Lovelace and Blackwell). Older architectures have not been tested but they may still work (Maxwell and Kepler)
- NVIDIA GPU drivers installed

## Helper pre-requisite installer

If you have an older version of python and need to update nvidia drivers, you can run:

```bash
sudo apt update

# (only if not present) install nvidia drivers
sudo apt install nvidia-driver-570 -y

# (only if python < 3.12) upgrade python to version +3.12
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 -y
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

## Installing dependencies

In this example we are using Ubuntu 24.04 LTS as a base OS, but this will work with any debian-based distribution too.

```bash
sudo apt update

# (only if not present) install python dependencies
sudo apt install python3-pip python3-venv python3-dev -y

# install docker
sudo apt-get update
sudo apt-get install ca-certificates curl gcc-14 -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo usermod -aG docker $USER

# install nvidia container runtime
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.17.8-1
sudo apt-get install -y \
    nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}

echo "REBOOT REQUIRED! Run: sudo shutdown -r now"
```

Once the node is configured, it can join the Kalavai pool as usual:

```bash
# install kalavai-client
python3 -m venv myenv
source myenv/bin/activate
pip install kalavai-client

# join the network
kalavai auth <user_id>
kalavai pool join <token>
```

See our [getting started guide](getting_started.md) for more information about the joining process.