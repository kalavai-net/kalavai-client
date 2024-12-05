#!/bin/bash

## Building llamacpp is required to avoid Illegal instruction errors
## Compiling it in runtime ensures the CPU will contain required instructions

subcommand=$1
shift

case "$subcommand" in
  worker)
    cd /workspace/llama.cpp
    mkdir build

    # GGML_RPC=ON: Builds RPC support
    # BUILD_SHARED_LIBS=OFF: Don't rely on shared libraries like libggml
    # use -DGGML_CUDA=ON for GPU support
    cmake . -DGGML_RPC=ON -DBUILD_SHARED_LIBS=OFF
    cmake --build . --config Release --parallel 1

    ldd bin/rpc-server
    ;;

  leader)
    source /workspace/env/bin/activate
    CMAKE_ARGS="-DLLAMA_RPC=on" pip3 install llama-cpp-python[server] --no-cache-dir
    ;;

  *)
    echo "unknown subcommand: $subcommand"
    exit 1
    ;;
esac