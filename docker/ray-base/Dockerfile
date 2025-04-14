FROM rayproject/ray:2.43.0-py310-gpu AS compile-image

WORKDIR $HOME/workspace

RUN sudo apt update && sudo apt install --no-install-recommends -y build-essential gcc

RUN python3 -m venv $HOME/workspace/env
RUN . $HOME/workspace/env/bin/activate && \
    pip3 install ray[serve-grpc,default]==2.43.0 --no-cache-dir

COPY download_hf.py .
COPY download_model.sh .
COPY ray_init.sh .

RUN sudo chmod +x $HOME/workspace/ray_init.sh
RUN sudo chmod +x $HOME/workspace/download_model.sh
