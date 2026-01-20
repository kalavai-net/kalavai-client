FROM python:3.12-slim

RUN apt update && apt install python3-dev gcc curl -y

RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4
RUN chmod 700 get_helm.sh
RUN ./get_helm.sh

WORKDIR /app

COPY . /app/

RUN pip install . --no-cache-dir

ENTRYPOINT ["python", "kalavai_client/api.py"]