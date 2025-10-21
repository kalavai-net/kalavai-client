FROM python:3.10-slim

RUN apt update && apt install -y curl wget

WORKDIR /workspace

COPY wait_for_service.sh .
COPY delete_model.py .
COPY register_model.sh .
COPY event_generator.py .
COPY requirements.txt .
COPY start_point.sh .
COPY cleanup.sh .

RUN pip3 install -r requirements.txt

RUN chmod +x /workspace/wait_for_service.sh
RUN chmod +x /workspace/register_model.sh
RUN chmod +x /workspace/start_point.sh
RUN chmod +x /workspace/cleanup.sh

