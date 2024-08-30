#!/bin/bash

# Connect to kalavai server via k3d
# TODO
set -e

BACKEND_ENDPOINT="https://kubeapi.test.k8s.mvp.kalavai.net"
KALAVAI_SERVER_URL="https://206.189.118.193:6443"
SERVER_TOKEN="K10fb2a18ef7a57b5222ecd43adff3834cf758120055b89e82e730878cdf891ca15::server:088a4cc9ef82e2942a2b7d16aebb048d"

# elevate to sudo if not already
SUDO=sudo
if [ $(id -u) -eq 0 ]; then
    SUDO=
fi

# --- helper functions for logs ---
info()
{
    echo '[INFO] ' "$@"
}
warn()
{
    echo '[WARN] ' "$@" >&2
}
fatal()
{
    echo '[ERROR] ' "$@" >&2
    exit 1
}

intro() {
    info "Kalavai installer. If you don't have one already, go to https://platform.kalavai.net and register for a free account."
}

# --- fatal if no systemd or openrc ---
verify_system() {
    if [ -x /sbin/openrc-run ]; then
        HAS_OPENRC=true
        return
    fi
    if [ -x /bin/systemctl ] || type systemctl > /dev/null 2>&1; then
        HAS_SYSTEMD=true
        return
    fi
    fatal 'Can not find systemd or openrc to use as a process supervisor for kalavai'
}
# --- validate user ---
validate_user() {
    # validate user-password
    $SUDO apt install -y curl jq
    read -p "Login email: " USEREMAIL
    stty -echo
    read -p "Password: " PASSWORD
    stty echo
    USER_NAME=$(curl -X POST $BACKEND_ENDPOINT/v1/validate_user -H 'Content-Type: application/json' -d '{"email":"'$USEREMAIL'", "password":"'$PASSWORD'"}' | jq -r ".username")
    echo $USER_NAME
}

# --- install dependencies ---
install_core_dependencies() {
    # echo "Installing package dependencies..."
    # # wireguard, open iscsi
    $SUDO apt install -y wireguard open-iscsi

    # docker
    # Add Docker's official GPG key:
    $SUDO apt-get update
    $SUDO apt-get install ca-certificates curl
    $SUDO install -m 0755 -d /etc/apt/keyrings
    $SUDO curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    $SUDO chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    $SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null
    $SUDO apt-get update
    $SUDO apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    $SUDO groupadd docker
    $SUDO usermod -aG docker $USER
    newgrp docker
    $SUDO nvidia-ctk runtime configure --runtime=docker
    $SUDO systemctl restart docker

    info "Installing nvidia runtime..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | $SUDO gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
      && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        $SUDO tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    $SUDO apt-get update
    $SUDO apt-get install -y nvidia-container-toolkit
}
# --- install kalavai client and connect
install_client() {
    # TODO: move it to an installable, so users can "kalavai start" / "kalavai stop"
    info "Connecting $HOSTNAME to Kalavai..."
    USER_NAME=$(validate_user)
    # nodes must be labelled for nvidia daemon (gpu=true) only if nvidia GPU is present
    gpu=$(lspci | grep -i '.* vga .* nvidia .*')
    shopt -s nocasematch
    if [[ $gpu == *'nvidia'* ]]; then
        LABELS="gpu=true"
    else
        LABELS="gpu=false"
    fi
    echo $LABELS
    # K3D_FIX_MOUNTS required to solve shared mounts https://github.com/k3d-io/k3d/pull/1268
    K3D_FIX_MOUNTS=1 k3d node create $USER_NAME-$(hostname) --token $SERVER_TOKEN --role agent  --cluster $KALAVAI_SERVER_URL --image docker.io/bundenth/k3s_cuda:v7 --k3s-node-label "$LABELS"
    info "Kalavai-client has been successfully installed on your computer!"
}


# --- run the install process --
{
    intro
    #verify_system
    #install_core_dependencies
    install_client
}
