# Steps required to install pre-requisites on an AMD GPU machine
# Minimum requirements:
    # OS: Linux
    # Python: 3.10 - 3.12
    # GPU: MI200s (gfx90a), MI300 (gfx942), Radeon RX 7900 series (gfx1100)
    # ROCm 6.2
    # Docker

# base OS: Ubuntu 24.04 LTS (debian-based)

# install docker
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# install python3.10+ (dev and venv)
sudo apt install python3.10-venv
sudo apt install python3-dev

# install ROCm 6.4
wget https://repo.radeon.com/amdgpu-install/6.4/ubuntu/noble/amdgpu-install_6.4.60400-1_all.deb
sudo apt install ./amdgpu-install_6.4.60400-1_all.deb 
sudo apt update
sudo apt install python3-setuptools python3-wheel
sudo usermod -a -G render,video $LOGNAME # Add the current user to the render and video groups
sudo apt install rocm

# install AMD-GPU driver
sudo apt install "linux-headers-$(uname -r)" "linux-modules-extra-$(uname -r)"
sudo apt install amdgpu-dkms

# install kalavai-client
python3 -m venv myenv
source myenv/bin/activate
pip install kalavai-client

# Join network
kalavai auth <user_id>
kalavai pool join <token>