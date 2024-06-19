set -e

VERSION="0.1.2"

# elevate to sudo if not already
SUDO=sudo
if [ $(id -u) -eq 0 ]; then
    SUDO=
fi

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

# get package installer
declare -A osInfo;
osInfo[/etc/debian_version]="apt-get"
osInfo[/etc/alpine-release]="apk"
osInfo[/etc/centos-release]="yum"
osInfo[/etc/fedora-release]="dnf"

for f in ${!osInfo[@]}
do
    if [[ -f $f ]];then
        package_manager=${osInfo[$f]}
    fi
done

if [ "$package_manager" == "apk" ]; then
    $SUDO $package_manager add -y wget rpm wireguard
else
    $SUDO $package_manager install -y wget wireguard
fi


if [ "$package_manager" == "apt-get" ]; then
    # Debian installers (deb) - apt-get
    wget https://github.com/kalavai-net/kalavai-client/releases/download/v${VERSION}/kalavai_${VERSION}_amd64.deb -O kalavai_${VERSION}_amd64.deb
    $SUDO dpkg -i ./kalavai_${VERSION}_amd64.deb
    $SUDO apt-get install -f
    $SUDO rm kalavai_${VERSION}_amd64.deb
else
    # RedHat installers (rpm) - yum dnf apk
    wget https://github.com/kalavai-net/kalavai-client/releases/download/v${VERSION}/kalavai-${VERSION}-1.x86_64.rpm -O kalavai-${VERSION}-1.x86_64.rpm
    $SUDO rpm -ivh ./kalavai-${VERSION}-1.x86_64.rpm
    $SUDO rm kalavai-${VERSION}-1.x86_64.rpm
fi

echo "Run Kalavai client and start sharing and earning with 'kalavai start'"







