# Base Ray image

Base image for templates that need ray installed.

```bash
podman buildx create --use --name arm64_builder
podman buildx build --push -t ghcr.io/kalavai-net/ray-base:latest --platform=linux/arm64,linux/amd64 .
```

Includes:
- CUDA drivers
- Ray backend
- Utility scripts for ray deployment
