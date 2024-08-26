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