FROM rayproject/ray:2.36.0-py310-gpu
COPY ray_init.sh /vllm-workspace/ray_init.sh

RUN pip3 install aphrodite-engine
RUN pip3 install huggingface_hub


COPY download_hf.py /vllm-workspace/download_hf.py

WORKDIR /vllm-workspace

RUN sudo chmod +x /vllm-workspace/ray_init.sh
