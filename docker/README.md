# Build images to GHCR

## Locally

echo "YOUR_TOKEN" | podman login ghcr.io -u <username> --password-stdin
podman build -t ghcr.io/kalavai-net/<image>:<tag> .
podman push ghcr.io/kalavai-net/<image>:<tag>


## CI/CD

GitHub action.


## External re-tagging

### Netclient

Move existing images from podman hub to GHCR to avoid quota limitations

```bash
podman pull gravitl/netclient:v0.90.0
podman tag gravitl/netclient:v0.90.0 ghcr.io/kalavai-net/netclient:v0.90.0
podman push ghcr.io/kalavai-net/netclient:v0.90.0
```
