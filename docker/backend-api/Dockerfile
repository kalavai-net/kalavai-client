FROM python:3.12-slim

RUN apt update && apt install -y gcc

RUN pip install kalavai-client>=0.6.2

ENTRYPOINT ["kalavai"]