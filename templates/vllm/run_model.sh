#!/bin/bash

cache_dir="/cache"

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
    --lora_modules=*)
      lora_modules="${1#*=}"
      ;;
    --cache_dir=*)
      cache_dir="${1#*=}"
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

if [ -z "$lora_modules" ]
then
  lora=""
else
  # download each lora adaptor, then create lora modules string
  IFS=';' read -r -a loras <<< "$lora_modules" # split into array
  all_loras=()
  for lora in "${loras[@]}"
  do
      if [ -z $lora ]; then
        continue
      fi
      # download
      dir=$cache_dir"/"$lora
      huggingface-cli download \
        $lora \
        --local-dir $dir \
        --local-dir-use-symlinks False

      # convert to lora string https://docs.vllm.ai/en/v0.5.5/models/lora.html#serving-lora-adapters
      safe_lora=`echo $lora | tr /- _`
      all_loras+=("${safe_lora}=${dir}")

      function join_by {
        local d=${1-} f=${2-}
        if shift 2; then
          printf %s "$f" "${@/#/$d}"
        fi
      }
  done
  lora="--enable-lora --lora-modules "$(join_by " " "${all_loras[@]}")
fi

python -m vllm.entrypoints.openai.api_server \
  --model $model_id \
  --host 0.0.0.0 --port 8080 \
  --tensor-parallel-size $tensor_parallel_size \
  --pipeline-parallel-size $pipeline_parallel_size \
  $lora \
  $extra
