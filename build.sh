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
fpm -s dir -t deb -d wireguard -d nvidia-container-toolkit -d netclient --name kalavai --force &&
fpm -s dir -t rpm -d wireguard-tools -d netclient -d nvidia-container-toolkit --name kalavai --force && 
mv -i *.deb ../ &&
mv -i *.rpm ../
