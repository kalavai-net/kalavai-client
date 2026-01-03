# Steps required to install pre-requisites on an AMD GPU machine
# Minimum requirements:
    # OS: Linux; kernel <= 6.11
    # Python: 3.10 - 3.12
    # GPU: MI200s (gfx90a), MI300 (gfx942), Radeon RX 7900 series (gfx1100)
    # ROCm 6.4.2


# base OS: Ubuntu 24.04 LTS (debian-based)

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
# optional
sudo usermod -aG docker $USER

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