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
# install podman
sudo apt-get update
sudo apt-get install ca-certificates curl gcc-14 -y
sudo apt-get -y install podman

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