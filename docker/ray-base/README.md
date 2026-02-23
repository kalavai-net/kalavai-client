# Base Ray image

Base image for templates that need ray installed.

```bash
docker build -t ghcr.io/kalavai-net/ray-base:latest .
docker push ghcr.io/kalavai-net/ray-base:latest
```

Includes:
- CUDA drivers
- Ray backend
- Utility scripts for ray deployment
