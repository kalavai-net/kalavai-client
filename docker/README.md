## Prerequisites

Containerd
nvidia container toolkit

wget https://github.com/containerd/containerd/releases/download/v1.6.8/containerd-1.6.8-linux-amd64.tar.gz
sudo tar Cxzvf /usr/local containerd-1.6.8-linux-amd64.tar.gz
wget https://github.com/opencontainers/runc/releases/download/v1.1.3/runc.amd64
sudo install -m 755 runc.amd64 /usr/local/sbin/runc
wget https://github.com/containernetworking/plugins/releases/download/v1.1.1/cni-plugins-linux-amd64-v1.1.1.tgz
sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.1.1.tgz
sudo mkdir /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml
sudo curl -L https://raw.githubusercontent.com/containerd/containerd/main/containerd.service -o /etc/systemd/system/containerd.service
sudo systemctl daemon-reload
sudo systemctl enable --now containerd

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=containerd
sudo systemctl restart containerd


Install version <= 5.6.0 of k3d:

```bash
wget -q -O - https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | TAG=v5.6.0 bash
```

Build docker image:
```bash
docker build -t k3s_cuda .
docker tag k3s_cuda:latest bundenth/k3s_cuda:v8
docker push bundenth/k3s_cuda:v8
```

Test:
```bash
k3d cluster create gputest --image=bundenth/k3s_cuda:v8 --gpus=1
```

Server (k3s):

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.28.8+k3s1 sh - 
cp /etc/rancher/k3s/k3s.yaml .kube/config
kubectl create -f device-plugin-daemonset.yaml
cat /var/lib/rancher/k3s/server/node-token # --> join TOKEN
```

Connect:
```bash
K3D_FIX_MOUNTS=1 k3d node create carlosfm-laptop --token K106dc0b7a2afe1c37557b0d53b59f0e3d73c8a29100fa1e2917c7cee47eab6ccf9::server:0407f04f6ee9b8cefa0376cadc326205 --role agent  --cluster https://167.99.94.158:6443 --image bundenth/k3s_cuda:v8
```
