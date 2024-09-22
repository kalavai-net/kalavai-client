Build docker image:
```bash
docker build -t ray-vllm .
docker tag ray-vllm:latest bundenth/ray-vllm:v1
docker push bundenth/ray-vllm:v1
```
