#!/bin/bash

while [ $# -gt 0 ]; do
  case "$1" in
    --model_path=*)
      model_path="${1#*=}"
      ;;
    --model_id=*)
      model_id="${1#*=}"
      ;;
    --quantization=*)
      quantization="${1#*=}"
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

python -m aphrodite.endpoints.openai.api_server  \
    --model $model_path \
    --served-model-name $model_id \
    --port 8080 --host 0.0.0.0 \
    --tensor-parallel-size $tensor_parallel_size \
    --pipeline-parallel-size $pipeline_parallel_size \
    $extra
