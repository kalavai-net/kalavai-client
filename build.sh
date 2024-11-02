set -e

# TODO:
# - right OPENSSL version (not the one on ubuntu 24 or pop-os)
# - low enough version of GCC

# - checks: building from a built environment
# TODO: rebuild?
source env/bin/activate

# - Checks: python <= 3.10
PYTHON_MAJOR=$(python -c 'import sys; print(sys.version_info[0])')
PYTHON_MINOR=$(python -c 'import sys; print(sys.version_info[1])')
if [ $PYTHON_MAJOR -ne 3 ]; then
    echo "[ERROR] Python version should be <=3.10, but it is "$PYTHON_MAJOR"."$PYTHON_MINOR
    exit
fi
if [ $PYTHON_MINOR -gt 10 ]; then
    echo "[ERROR] Python version should be <=3.10, but it is "$PYTHON_MAJOR"."$PYTHON_MINOR
    exit
fi

export DEBEMAIL="carlos@kalavai.net"
export DEBFULLNAME="Kalavai.net"
export APP_NAME="kalavai"
echo "## GENERATE BINARY"
rm -r build
mkdir -p dist
pyinstaller -y --clean kalavai_client/cli.py --onefile --name $APP_NAME --add-data="assets/:assets/" --bootloader-ignore-signals
rm $APP_NAME.spec

echo "One file executable available at dist/${APP_NAME}"

echo "## GENERATE INSTALLABLE with FPM"
# can add dependencies by passing -d name to fpm
cd build_specs &&
fpm -s dir -t deb -d wireguard -d nvidia-container-toolkit --name kalavai --force &&
fpm -s dir -t rpm -d wireguard-tools -d netclient -d nvidia-container-toolkit --name kalavai --force && 
mv -i *.deb ../ &&
mv -i *.rpm ../

cd ..
deactivate