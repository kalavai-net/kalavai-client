#!/bin/bash
set -e

# TODO: fetch these values dynamically from the server?
BACKEND_ENDPOINT="https://kubeapi.test.k8s.mvp.kalavai.net"
KALAVAI_SERVER_URL="https://178.62.13.8:6443"
SERVER_TOKEN="K104e6a6f028741b363d3e8f699960b8b641c2ceb4d69ce1bbcd95d4ba082cfa377::server:3deea328ae7deaecc319653e4d9d36a4"

echo "\n"
echo "Kalavai installer. If you don't have one already, go to https://platform.kalavai.net and register for a free account."
echo "\n"

# validate user-password
sudo apt install -y curl
echo "Login email: "
read USEREMAIL
echo "Password "
stty -echo
read PASSWORD
stty echo
USER_NAME=$(curl -X POST $BACKEND_ENDPOINT/v1/validate_user -H 'Content-Type: application/json' -d '{"email":"'$USEREMAIL'", "password":"'$PASSWORD'"}' | jq -r ".username")
echo $USER_NAME" validated!"

# echo "Installing package dependencies..."
# # wireguard, open iscsi
sudo apt install -y wireguard open-iscsi

# docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo "Installing nvidia runtime..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit


# TODO: move it to an installable, so users can "kalavai start" / "kalavai stop"
echo "Connecting $HOSTNAME to Kalavai..."
curl -sfL https://get.k3s.io | K3S_URL=$KALAVAI_SERVER_URL K3S_TOKEN=$SERVER_TOKEN K3S_NODE_NAME=$USER_NAME-$(hostname) sh -

echo "\n"
echo "Kalavai-client has been successfully installed on your computer!"
