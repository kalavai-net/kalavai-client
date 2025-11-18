# Base Ray image

Base image for templates that need ray installed.

```bash
docker build -t kalavai/ray-base:latest .
docker push kalavai/ray-base:latest
```

Includes:
- CUDA drivers
- Ray backend
- Utility scripts for ray deployment
