# Build images to GHCR

## Locally

echo "YOUR_TOKEN" | docker login ghcr.io -u <username> --password-stdin
docker build -t ghcr.io/kalavai-net/<image>:<tag> .
docker push ghcr.io/kalavai-net/<image>:<tag>


## CI/CD

GitHub action.


## External re-tagging

### Netclient

Move existing images from docker hub to GHCR to avoid quota limitations

```bash
docker pull gravitl/netclient:v0.90.0
docker tag gravitl/netclient:v0.90.0 ghcr.io/kalavai-net/netclient:v0.90.0
docker push ghcr.io/kalavai-net/netclient:v0.90.0
```
