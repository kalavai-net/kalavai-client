FROM rayproject/ray:2.36.0-py310-gpu
COPY ray_init.sh /vllm-workspace/ray_init.sh

RUN pip3 install aphrodite-engine
# workaround dependency issue with gguf https://github.com/PygmalionAI/aphrodite-engine/issues/783
RUN pip3 install gguf==0.10.0 
RUN pip3 install huggingface_hub


COPY download_hf.py /vllm-workspace/download_hf.py
COPY run_model.sh /vllm-workspace/run_model.sh

WORKDIR /vllm-workspace

RUN sudo chmod +x /vllm-workspace/ray_init.sh
RUN sudo chmod +x /vllm-workspace/run_model.sh