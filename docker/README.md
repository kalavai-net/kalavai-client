# Build images to GHCR

## Locally

echo "YOUR_TOKEN" | docker login ghcr.io -u <username> --password-stdin
docker build -t ghcr.io/kalavai-net/<image>:<tag> .
docker push ghcr.io/kalavai-net/<image>:<tag>


## CI/CD

GitHub action.