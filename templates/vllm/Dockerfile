# FROM rayproject/ray:2.39.0-py310-gpu AS compile-image

# WORKDIR $HOME/workspace

# RUN sudo apt update && sudo apt install --no-install-recommends -y build-essential gcc

# RUN python3 -m venv $HOME/workspace/env
# RUN . $HOME/workspace/env/bin/activate && \
#     pip3 install vllm --no-cache-dir && \
#     pip3 install ray[serve-grpc]==2.39.0 --no-cache-dir


FROM bundenth/ray:latest AS build-image

RUN sudo apt update && sudo apt install bc

RUN . $HOME/workspace/env/bin/activate && \
    pip3 install "vllm==0.6.4" --no-cache-dir && \
    pip3 install huggingface-hub --no-cache-dir

WORKDIR $HOME/workspace

COPY ray_init.sh .
COPY run_model.sh .
COPY download_model.sh .
COPY download_hf.py .

RUN sudo chmod +x $HOME/workspace/ray_init.sh
RUN sudo chmod +x $HOME/workspace/run_model.sh
RUN sudo chmod +x $HOME/workspace/download_model.sh

CMD . $HOME/workspace/env/bin/activate
