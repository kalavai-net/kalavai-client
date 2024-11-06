FROM rayproject/ray:2.36.0-py310-gpu AS compile-image

WORKDIR $HOME/workspace

RUN sudo apt update && sudo apt install --no-install-recommends -y build-essential gcc

RUN python3 -m venv $HOME/workspace/env
# workaround dependency issue with gguf https://github.com/PygmalionAI/aphrodite-engine/issues/783
RUN . $HOME/workspace/env/bin/activate && \
    pip3 install aphrodite-engine --no-cache-dir && \
    pip3 install gguf==0.10.0 --no-cache-dir && \
    pip3 install huggingface_hub --no-cache-dir && \
    pip3 install ray[serve-grpc]==2.36.0

COPY ray_init.sh .
COPY download_hf.py .
COPY run_model.sh .


FROM rayproject/ray:2.36.0-py310-gpu AS build-image

RUN sudo apt update && sudo apt install bc

WORKDIR $HOME/workspace

COPY --from=compile-image $HOME/workspace $HOME/workspace

RUN sudo chmod +x $HOME/workspace/ray_init.sh
RUN sudo chmod +x $HOME/workspace/run_model.sh

CMD . $HOME/workspace/env/bin/activate
