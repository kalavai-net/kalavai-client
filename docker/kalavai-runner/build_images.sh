#!/bin/bash

K3S_TAG="v1.34.1-k3s1"
TEMPLATE_VERSION=1

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --version) K3S_TAG="$2" ;;
        --template-version) TEMPLATE_VERSION="$2" ;;
    esac
    shift
done


IMAGE_TAG="${K3S_TAG}-${TEMPLATE_VERSION}"
AMD_TAGS=(-t ghcr.io/kalavai-net/kalavai-runner-amd64:$IMAGE_TAG)
AMD_TAGS+=(-t ghcr.io/kalavai-net/kalavai-runner-amd64:latest)

docker buildx build --build-arg K3S_TAG=$K3S_TAG --push \
  "${AMD_TAGS[@]}" --platform=linux/amd64 \
  -f Dockerfile_amd64 .

ARM_TAGS=(-t ghcr.io/kalavai-net/kalavai-runner-arm64:$IMAGE_TAG)
ARM_TAGS+=(-t ghcr.io/kalavai-net/kalavai-runner-arm64:latest)

docker buildx build --build-arg K3S_TAG=$K3S_TAG --push \
  "${ARM_TAGS[@]}" --platform=linux/arm64 \
  -f Dockerfile_arm64 .