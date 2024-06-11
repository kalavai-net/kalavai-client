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
sudo yum install -y curl
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
sudo yum install -y iscsi-initiator-utils
sudo dnf install -y wireguard-tools

# docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Install NVIDIA container runtime
echo "Installing nvidia runtime..."
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
sudo yum install -y nvidia-container-toolkit


# TODO: move it to an installable, so users can "kalavai start" / "kalavai stop"
echo "Connecting $HOSTNAME to Kalavai..."
curl -sfL https://get.k3s.io | K3S_URL=$KALAVAI_SERVER_URL K3S_TOKEN=$SERVER_TOKEN K3S_NODE_NAME=$USER_NAME-$(hostname) sh -

echo "\n"
echo "Kalavai-client has been successfully installed on your computer!"
