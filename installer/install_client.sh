set -e

# get version (if set)
if [[ -z "${KALAVAI_VERSION}" ]]; then
    # set to latest
    KALAVAI_VERSION="v0.1.8"
else
    KALAVAI_VERSION="${KALAVAI_VERSION}"
fi

# elevate to sudo if not already
SUDO=sudo
if [ $(id -u) -eq 0 ]; then
    SUDO=
fi
# get package installer
declare -A osInfo;
osInfo[/etc/debian_version]="apt-get"
osInfo[/etc/centos-release]="yum"
osInfo[/etc/fedora-release]="dnf"
osInfo[/etc/SuSE-release]="zypper"

for f in ${!osInfo[@]}
do
    if [[ -f $f ]];then
        package_manager=${osInfo[$f]}
    fi
done

# --- helper functions for logs ---
info()
{
    echo '[INFO] ' "$@"
}
fatal()
{
    echo '[ERROR] ' "$@" >&2
    exit 1
}
# --- set arch and suffix, fatal if architecture not supported ---
setup_verify_arch() {
    if [ -z "$ARCH" ]; then
        ARCH=$(uname -m)
    fi
    case $ARCH in
        amd64)
            ARCH=amd64
            SUFFIX=
            ;;
        x86_64)
            ARCH=amd64
            SUFFIX=
            ;;
        *)
            fatal "Unsupported architecture $ARCH"
    esac
}
# --- install dependencies ---
install_core_dependencies() {
    info "Installing package dependencies..."
    info "Installing nvidia runtime..."
    # nvidia-container-runtime, wireguard, open-iscsi, containerd
    $SUDO $package_manager install -y curl jq wget
    if [ "$package_manager" == "apt-get" ]; then
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | $SUDO gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            $SUDO tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
        $SUDO $package_manager update
        $SUDO $package_manager install -y nvidia-container-toolkit wireguard open-iscsi nfs-common

    elif [ "$package_manager" == "yum" ]; then
        curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
            $SUDO tee /etc/yum.repos.d/nvidia-container-toolkit.repo
        $SUDO $package_manager install -y nvidia-container-toolkit iscsi-initiator-utils nfs-utils
        $SUDO $package_manager install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm https://www.elrepo.org/elrepo-release-8.el8.elrepo.noarch.rpm
        $SUDO $package_manager install -y kmod-wireguard wireguard-tools

    elif [ "$package_manager" == "dnf" ]; then
        curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
            $SUDO tee /etc/yum.repos.d/nvidia-container-toolkit.repo
        $SUDO $package_manager install -y nvidia-container-toolkit wireguard-tools iscsi-initiator-utils nfs-utils

    elif [ "$package_manager" == "zypper" ]; then
        $SUDO $package_manager ar https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo
        $SUDO $package_manager --gpg-auto-import-keys install -y nvidia-container-toolkit
        $SUDO $package_manager install -y wireguard-tools open-iscsi

    else
        fatal "Package manager is not recognised"
    fi
    
    # enable Open ISCSI
    $SUDO systemctl enable --now iscsid

    # install containerd
    wget https://github.com/containerd/containerd/releases/download/v1.7.18/containerd-1.7.18-linux-amd64.tar.gz -O containerd-1.7.18-linux-amd64.tar.gz
    $SUDO tar Cxzvf /usr/local containerd-1.7.18-linux-amd64.tar.gz
    wget https://raw.githubusercontent.com/containerd/containerd/main/containerd.service -O containerd.service
    $SUDO mkdir -p /usr/local/lib/systemd/system/
    $SUDO mv containerd.service /usr/local/lib/systemd/system/
    $SUDO systemctl daemon-reload
    $SUDO systemctl enable --now containerd
    wget https://github.com/opencontainers/runc/releases/download/v1.1.13/runc.amd64 -O runc.amd64
    $SUDO install -m 755 runc.amd64 /usr/local/sbin/runc
    wget https://github.com/containernetworking/plugins/releases/download/v1.5.1/cni-plugins-linux-amd64-v1.5.1.tgz -O cni-plugins-linux-amd64-v1.5.1.tgz
    $SUDO mkdir -p /opt/cni/bin
    $SUDO tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.5.1.tgz

    # cleanup
    rm containerd-1.7.18-linux-amd64.tar.gz
    rm cni-plugins-linux-amd64-v1.5.1.tgz
    rm runc.amd64

    # install helmfile
    wget https://github.com/helmfile/helmfile/releases/download/v0.167.1/helmfile_0.167.1_linux_amd64.tar.gz
    mkdir helmfile && tar -xvzf helmfile_0.167.1_linux_amd64.tar.gz -C helmfile
    $SUDO mv helmfile/helmfile /usr/local/bin/
    $SUDO rm -r helmfile
    $SUDO rm helmfile_0.167.1_linux_amd64.tar.gz

    # configure containerd for nvidia
    # PRODUCES ERRO[0000] unrecognized runtime 'containerd'
    $SUDO nvidia-ctk runtime configure --runtime=containerd
    $SUDO systemctl restart containerd

    echo "# TACKLE "too many files open" in kubernetes pods
fs.inotify.max_user_watches = 655360
fs.inotify.max_user_instances = 1280"  | sudo tee -a /etc/sysctl.conf

}
install_kalavai_app() {
    if [ "$package_manager" == "apt-get" ]; then
        # Debian installers (deb) - apt-get
        wget https://github.com/kalavai-net/kalavai-client/releases/download/${KALAVAI_VERSION}/kalavai_${KALAVAI_VERSION}_amd64.deb -O kalavai_${KALAVAI_VERSION}_amd64.deb
        $SUDO dpkg -i ./kalavai_${KALAVAI_VERSION}_amd64.deb
        $SUDO apt-get install -f
        $SUDO rm kalavai_${KALAVAI_VERSION}_amd64.deb
    else
        # RedHat installers (rpm) - yum dnf apk
        wget https://github.com/kalavai-net/kalavai-client/releases/download/${KALAVAI_VERSION}/kalavai-${KALAVAI_VERSION}-1.x86_64.rpm -O kalavai-${KALAVAI_VERSION}-1.x86_64.rpm
        $SUDO rpm -ivh ./kalavai-${KALAVAI_VERSION}-1.x86_64.rpm
        $SUDO rm kalavai-${KALAVAI_VERSION}-1.x86_64.rpm
    fi
}
success() {
    info "----------------------------------------------------"
    info "*** Kalavai app has been successfully installed! ***"
    info "*** Start sharing and earning with 'kalavai start' ***"
    info "----------------------------------------------------"
}


{
    setup_verify_arch
    install_core_dependencies
    install_kalavai_app
    success
}






