FROM python:3.10-slim

RUN apt update && apt install -y curl wget

RUN pip3 install requests 

WORKDIR /workspace

COPY wait_for_service.sh .
COPY get_litellm_id.py .
COPY register_model.sh .

RUN chmod +x /workspace/wait_for_service.sh
RUN chmod +x /workspace/register_model.sh

