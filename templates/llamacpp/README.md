# Distributed llama.cpp 

https://github.com/ggerganov/llama.cpp/tree/master/examples/rpc

Two docker images:
- server: llama-cpp-python API server that serves the model and connects to the RPC workers
- worker: llama-cpp built with RPC=ON.

To support GPU, worker image must be built against adequate drivers.
