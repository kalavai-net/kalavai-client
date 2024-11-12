#!/bin/bash

while [ $# -gt 0 ]; do
  case "$1" in
    --model_id=*)
      model_id="${1#*=}"
      ;;
    --tensor_parallel_size=*)
      tensor_parallel_size="${1#*=}"
      ;;
    --pipeline_parallel_size=*)
      pipeline_parallel_size="${1#*=}"
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

source /home/ray/workspace/env/bin/activate

python -m vllm.entrypoints.openai.api_server \
    --host 0.0.0.0 --port 8080 \
    --tensor-parallel-size $tensor_parallel_size \
    --pipeline-parallel-size $pipeline_parallel_size \
    --model $model_id \
    $extra
