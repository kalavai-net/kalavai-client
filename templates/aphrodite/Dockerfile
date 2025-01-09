FROM bundenth/ray:latest AS build-image

RUN sudo apt update && sudo apt install bc

# workaround dependency issue with gguf https://github.com/PygmalionAI/aphrodite-engine/issues/783
RUN . $HOME/workspace/env/bin/activate && \
    pip3 install aphrodite-engine --no-cache-dir && \
    pip3 install gguf==0.10.0 --no-cache-dir

WORKDIR $HOME/workspace

COPY run_model.sh .

RUN sudo chmod +x $HOME/workspace/run_model.sh

CMD . $HOME/workspace/env/bin/activate
