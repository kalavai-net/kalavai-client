FROM rayproject/ray:2.36.0-py310-gpu AS compile-image

WORKDIR $HOME/workspace

RUN sudo apt update && sudo apt install --no-install-recommends -y build-essential gcc

RUN python3 -m venv $HOME/workspace/env
RUN . $HOME/workspace/env/bin/activate && \
    pip3 install vllm --no-cache-dir && \
    pip3 install ray[serve-grpc]==2.36.0

COPY ray_init.sh .
COPY run_model.sh .


FROM rayproject/ray:2.36.0-py310-gpu AS build-image

RUN sudo apt update && sudo apt install bc

WORKDIR $HOME/workspace

COPY --from=compile-image $HOME/workspace $HOME/workspace

RUN sudo chmod +x $HOME/workspace/ray_init.sh
RUN sudo chmod +x $HOME/workspace/run_model.sh

CMD . $HOME/workspace/env/bin/activate
