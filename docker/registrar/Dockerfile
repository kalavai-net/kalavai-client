FROM python:3.12-slim

RUN apt update && apt install -y curl wget iputils-ping

WORKDIR /workspace

COPY wait_for_service.sh .
COPY delete_model.py .
COPY register_model.sh .
COPY requirements.txt .
COPY start_point.sh .
COPY cleanup.sh .
COPY wait_for_ping.sh .
COPY get_node_label_value.py .
COPY billing_heartbeat.py .

RUN pip3 install -r requirements.txt

RUN chmod +x /workspace/wait_for_service.sh
RUN chmod +x /workspace/register_model.sh
RUN chmod +x /workspace/start_point.sh
RUN chmod +x /workspace/cleanup.sh
RUN chmod +x /workspace/wait_for_ping.sh

