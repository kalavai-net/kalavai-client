# Image used to generate self-contained QCOW2 images
FROM nvidia/cuda:12.6.0-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive

ARG KALAVAI_TOKEN="none"
ARG KALAVAI_VERSION=0.7.23
ARG KALAVAI_NODE_TAGS="kalavai/type=qcow2"

WORKDIR /app

# install python
RUN apt-get update && \
    apt-get install -y curl git gcc wget build-essential python3-dev python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# install python dependencies
RUN python3 -m pip install "kalavai-client==${KALAVAI_VERSION}" --no-cache-dir --break-system-packages

# Generate run script
ARG RUN_SCRIPT_CONTENT="kalavai pool join $KALAVAI_TOKEN --non-interactive --node-labels=$KALAVAI_NODE_TAGS"

RUN echo $RUN_SCRIPT_CONTENT > run_kalavai.sh
RUN chmod +x run_kalavai.sh

ENTRYPOINT [ "run_kalavai.sh"]
