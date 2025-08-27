# Base Ray image

Base image for templates that need ray installed.

```bash
docker build -t bundenth/ray:latest .
docker push bundenth/ray:latest
```

Includes:
- CUDA drivers
- Ray backend
- Utility scripts for ray deployment
