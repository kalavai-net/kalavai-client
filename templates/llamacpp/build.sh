#!/bin/bash

## Building llamacpp is required to avoid Illegal instruction errors
## Compiling it in runtime ensures the CPU will contain required instructions

subcommand=$1
shift

case "$subcommand" in
  server_cpu)
    source /workspace/env/bin/activate
    CMAKE_ARGS="-DGGML_RPC=on" pip3 install llama-cpp-python[server]
    ;;
  server_gpu)
    source /workspace/env/bin/activate
    CMAKE_ARGS="-DGGML_RPC=on -DGGML_CUDA=on" pip3 install llama-cpp-python[server]
    ;;
  cpu)
    cd /workspace/llama.cpp
    mkdir build
    cd build

    # GGML_RPC=ON: Builds RPC support
    # BUILD_SHARED_LIBS=OFF: Don't rely on shared libraries like libggml
    # use -DGGML_CUDA=ON for GPU support
    cmake .. -DGGML_RPC=ON
    cmake --build . --config Release -j $(nproc)
    ;;
  
  gpu)
    cd /workspace/llama.cpp
    mkdir build
    cd build

    # GGML_RPC=ON: Builds RPC support
    # BUILD_SHARED_LIBS=OFF: Don't rely on shared libraries like libggml
    # use -DGGML_CUDA=ON for GPU support
    cmake .. -DGGML_RPC=ON -DGGML_CUDA=ON -DGGML_CUDA_ENABLE_UNIFIED_MEMORY=1
    cmake --build . --config Release -j $(nproc)
    ;;

  *)
    echo "unknown subcommand: $subcommand"
    exit 1
    ;;
esac