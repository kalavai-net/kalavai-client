#!/bin/bash

local_dir=/tmp
port=8080
extra=""

while [ $# -gt 0 ]; do
  case "$1" in
    --repo_id=*)
      repo_id="${1#*=}"
      ;;
    --model_filename=*)
      model_filename="${1#*=}"
      ;;
    --local_dir=*)
      local_dir="${1#*=}"
      ;;
    --rpc_servers=*)
      rpc_servers="${1#*=}"
      ;;
    --port=*)
      port="${1#*=}"
      ;;
    --extra=*)
      extra="${1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

source /workspace/env/bin/activate

#################
# download model #
#################
# alternatively, load with server python3 -m llama_cpp.server --hf_model_repo_id Qwen/Qwen2-0.5B-Instruct-GGUF --model '*q8_0.gguf'
huggingface-cli download \
    $repo_id \
    $model_filename \
    --local-dir $local_dir \
    --local-dir-use-symlinks False

## Create config ##
python /workspace/generate_config.py \
  --port $port --host 0.0.0.0 \
  --models-path $local_dir \
  --model-extension "*.gguf" \
  --output-filename /workspace/config.json

##################
# run API server #
##################
echo "Connecting to workers: "$rpc_servers

python -m llama_cpp.server \
  --config_file /workspace/config.json \
  --rpc_servers $rpc_servers \
  $extra

# /workspace/llama.cpp/build/bin/llama-server --list-devices
# /workspace/llama.cpp/build/bin/llama-server \
#   --port $port \
#   --host 0.0.0.0 \
#   --model $local_dir/$model_filename \
#   --rpc $rpc_servers \
#   $extra
