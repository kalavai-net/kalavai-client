FROM python:3.10

RUN apt update && apt install iputils-ping -y

WORKDIR /workspace

COPY . .

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3" ]
CMD [ "keeper.py" ]