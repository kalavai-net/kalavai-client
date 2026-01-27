FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/kalavai-net/kalavai-client

RUN apt update && apt install python3-dev gcc curl wget -y

RUN wget https://github.com/helmfile/helmfile/releases/download/v0.159.0/helmfile_0.159.0_linux_amd64.tar.gz
RUN tar -xxf helmfile_0.159.0_linux_amd64.tar.gz
RUN rm helmfile_0.159.0_linux_amd64.tar.gz
RUN mv helmfile /usr/local/bin/

WORKDIR /app

COPY . /app/

RUN pip install . --no-cache-dir

ENTRYPOINT ["python", "kalavai_client/api.py"]