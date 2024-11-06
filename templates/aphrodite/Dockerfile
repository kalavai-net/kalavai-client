FROM rayproject/ray:2.36.0-py310-gpu AS compile-image

RUN sudo apt update && sudo apt install --no-install-recommends -y build-essential gcc bc

RUN python3 -m venv $HOME/workspace
ENV PATH="/$HOME/workspace/bin:$PATH"

RUN pip install aphrodite-engine
# workaround dependency issue with gguf https://github.com/PygmalionAI/aphrodite-engine/issues/783
RUN pip install gguf==0.10.0 
RUN pip install huggingface_hub

COPY ray_init.sh $HOME/workspace/ray_init.sh
COPY download_hf.py $HOME/workspace/download_hf.py
COPY run_model.sh $HOME/workspace/run_model.sh


FROM rayproject/ray:2.36.0-py310-gpu AS build-image

COPY --from=compile-image $HOME/workspace $HOME/workspace

ENV PATH="$HOME/workspace/bin:$PATH"

RUN sudo chmod +x $HOME/workspace/ray_init.sh
RUN sudo chmod +x $HOME/workspace/run_model.sh



# FROM rayproject/ray:2.36.0-py310-gpu

# RUN sudo apt update && sudo apt install bc
# RUN pip3 install aphrodite-engine
# # workaround dependency issue with gguf https://github.com/PygmalionAI/aphrodite-engine/issues/783
# RUN pip3 install gguf==0.10.0 
# RUN pip3 install huggingface_hub

# COPY ray_init.sh /vllm-workspace/ray_init.sh
# COPY download_hf.py /vllm-workspace/download_hf.py
# COPY run_model.sh /vllm-workspace/run_model.sh

# WORKDIR /vllm-workspace

# RUN sudo chmod +x /vllm-workspace/ray_init.sh
# RUN sudo chmod +x /vllm-workspace/run_model.sh