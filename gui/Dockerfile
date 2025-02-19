FROM python:3.12-slim

RUN apt update && apt install -y gcc unzip curl

WORKDIR /workspace/kalavai

COPY . .
RUN pip3 install -r requirements.txt

CMD ["reflex", "run"]