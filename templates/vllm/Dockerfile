FROM rayproject/ray:2.36.0-py310-gpu
COPY ray_init.sh /vllm-workspace/ray_init.sh

RUN pip3 install vllm

RUN sudo chmod +x /vllm-workspace/ray_init.sh
