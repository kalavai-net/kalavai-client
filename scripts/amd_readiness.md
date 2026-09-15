# Steps required to install pre-requisites on an AMD GPU machine
# Minimum requirements:
    # OS: Linux; kernel <= 6.11
    # Python: 3.10 - 3.12
    # GPU: MI200s (gfx90a), MI300 (gfx942), Radeon RX 7900 series (gfx1100)
    # ROCm 6.4.2


# base OS: Ubuntu 24.04 LTS (debian-based)

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

# install kalavai-client
python3 -m venv myenv
source myenv/bin/activate
pip install kalavai-client

# Join network
kalavai auth <user_id>
kalavai pool join <token>