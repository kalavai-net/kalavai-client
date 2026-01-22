# Dockerising kalavai


Custom k3d image including nvidia container toolkit
It also includes certain default deployments we want for all clusters


## Run

Server

k3d cluster create gputest --image=docker.io/kalavai/kalavai-base:gpu-latest --gpus=1

Worker

k3d node create k3d-worker --image docker.io/kalavai/kalavai-base:gpu-latest --cluster gputest




## pure docker

docker run   --privileged   --gpus all  --name k3s-server-1   --hostname k3s-server-1   -p 6443:6443 -p 31000:31000   -d kalavai/kalavai-base:gpu-latest   server
docker cp k3s-server-1:/etc/rancher/k3s/k3s.yaml ~/.kube/config

helm install nvidia-operator --wait \
     -n kalavai --create-namespace \
     kalavai/gpu


# Multi arch builder

Build and push for arm64 (mac, raspberry pi)

```bash
docker buildx create --use --name arm64_builder
docker buildx build --push -t ghcr.io/kalavai-net/kalavai-runner-arm64:latest --platform=linux/arm64 -f Dockerfile_arm64 .
```

51.159.184.238
51.159.150.27
51.159.165.245
