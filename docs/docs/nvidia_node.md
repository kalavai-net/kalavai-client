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

If you installed a new version and used update-alternatives to set python3, you may need to rewire the apt_pkg:

```bash
cd /usr/lib/python3/dist-packages/
ls apt_pkg.cpython*
sudo ln -s apt_pkg.cpython-310-x86_64-linux-gnu.so apt_pkg.so
```

## Installing dependencies

In this example we are using Ubuntu 24.04 LTS as a base OS, but this will work with any debian-based distribution too.

```bash
sudo apt update

# (only if not present) install python dependencies
sudo apt install python3-pip python3-venv python3-dev -y

# install podman
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt-get update
sudo apt-get -y install podman

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
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml

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