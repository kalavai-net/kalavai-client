FROM python:3.12-slim

RUN apt update && apt install python3-dev gcc -y

WORKDIR /app

COPY . /app/

RUN pip install . --no-cache-dir

ENTRYPOINT ["python", "kalavai_client/api.py"]