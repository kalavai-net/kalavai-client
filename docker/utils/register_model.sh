#!/bin/bash

cache_dir="/cache"
job_id="None"

while [ $# -gt 0 ]; do
  case "$1" in
    --litellm_base_url=*)
      litellm_base_url="${1#*=}"
      ;;
    --litellm_key=*)
      litellm_key="${1#*=}"
      ;;
    --litellm_model_name=*)
      litellm_model_name="${1#*=}"
      ;;
    --model_id=*)
      model_id="${1#*=}"
      ;;
    --provider=*)
      provider="${1#*=}"
      ;;
    --api_base=*)
      api_base="${1#*=}"
      ;;
    --model_info=*)
      model_info="${1#*=}"
      ;;
    --job_id=*)
      job_id="${1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

result=$(curl -X POST "$litellm_base_url/model/new" \
    -H 'Authorization: Bearer '$litellm_key \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d '{
          "model_name": "'$litellm_model_name'",
          "model_info": '"$model_info"',
          "litellm_params": {"drop_params": false, "model": "'$provider'/'$model_id'", "api_base": "'$api_base'", "api_key": "DUMMY", "job_id": "'$job_id'"}
        }' 2>&1)


if [[ $? -ne 0 ]]; then
    echo $result
    exit 1
else
    echo "Model registered successfully!"
    echo $result
    tail -f /dev/null
fi
