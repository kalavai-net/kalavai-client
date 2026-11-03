---
tags:
  - amd
  - rocm
---

# Pre-requisites

Kalavai platform supports the use of both NVIDIA and AMD cards. To ensure full compatibility, the worker node must have the following requirements met:

- OS: Linux; kernel <= 6.11
- Python: +3.12
- GPU: MI200s (gfx90a), MI300 (gfx942), Radeon RX 7900 series (gfx1100)
- ROCm 6.4.2

## Installing dependencies

In this example we are using Ubuntu 24.04 LTS as a base OS, but this will work with any debian-based distribution too.

```bash
# install docker
# Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# install nvidia container runtime
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.18.2-1
sudo apt-get install -y \
    nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}

sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# install python3.12+ (dev and venv)
sudo apt install python3.12-dev python3.12-venv -y

# install ROCm 6.4.2
wget https://repo.radeon.com/amdgpu-install/6.4.2/ubuntu/noble/amdgpu-install_6.4.60402-1_all.deb
sudo dpkg -i amdgpu-install_6.4.60402-1_all.deb 
sudo apt update && sudo apt install python3-setuptools python3-wheel -y
sudo usermod -a -G render,video $LOGNAME
sudo apt install rocm -y

# install AMD-GPU driver
sudo apt install "linux-headers-$(uname -r)" -y
sudo apt update && sudo apt install amdgpu-dkms -y

# Reboot machine
sudo reboot

# (optional) add rocm-smi and amd-smi to path (add to ~/.bashrc)
export PATH=$PATH:/opt/rocm-6.4.2/bin:/opt/rocm-6.4.2/libexec/rocm_smi
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