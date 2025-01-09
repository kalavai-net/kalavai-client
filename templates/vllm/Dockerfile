FROM bundenth/ray:latest AS build-image

RUN sudo apt update && sudo apt install bc

RUN . $HOME/workspace/env/bin/activate && \
    pip3 install "vllm==0.6.4" --no-cache-dir && \
    pip3 install huggingface-hub --no-cache-dir

WORKDIR $HOME/workspace

COPY run_model.sh .

RUN sudo chmod +x $HOME/workspace/run_model.sh

CMD . $HOME/workspace/env/bin/activate
