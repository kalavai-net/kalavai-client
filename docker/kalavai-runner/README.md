# Dockerising kalavai


Custom k3d image including nvidia container toolkit
It also includes certain default deployments we want for all clusters


## Run

Server

k3d cluster create gputest --image=podman.io/kalavai/kalavai-base:gpu-latest --gpus=1

Worker

k3d node create k3d-worker --image podman.io/kalavai/kalavai-base:gpu-latest --cluster gputest




## pure podman

podman run   --privileged   --gpus all  --name k3s-server-1   --hostname k3s-server-1   -p 6443:6443 -p 31000:31000   -d kalavai/kalavai-base:gpu-latest   server
podman cp k3s-server-1:/etc/rancher/k3s/k3s.yaml ~/.kube/config

helm install nvidia-operator --wait \
     -n kalavai --create-namespace \
     kalavai/gpu


# Multi arch builder

Build and push for arm64 (mac, raspberry pi)

bash build_images.sh --version v1.37.1-k3s1

