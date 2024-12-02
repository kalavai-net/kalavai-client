FROM rayproject/ray:2.39.0-py310-gpu AS compile-image

WORKDIR $HOME/workspace

RUN sudo apt update && sudo apt install --no-install-recommends -y build-essential gcc

RUN python3 -m venv $HOME/workspace/env
RUN . $HOME/workspace/env/bin/activate && \
    pip3 install ray[serve-grpc,default]==2.39.0 --no-cache-dir
