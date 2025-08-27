FROM rayproject/ray:2.43.0-py312-gpu AS compile-image

WORKDIR /home/ray/workspace

RUN sudo apt update && sudo apt install --no-install-recommends -y build-essential gcc

#RUN python3 -m venv /home/ray/workspace/env
#RUN . /home/ray/workspace/env/bin/activate && \
RUN pip install ray[serve-grpc,default]==2.43.0 huggingface-hub --no-cache-dir

COPY download_hf.py .
COPY download_model.sh .
COPY ray_init.sh .

RUN sudo chmod +x /home/ray/workspace/ray_init.sh
RUN sudo chmod +x /home/ray/workspace/download_model.sh
