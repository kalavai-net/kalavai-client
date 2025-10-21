#!/bin/bash

cache_dir="/cache"
job_id="None"
api_key="DUMMY"
litellm_kalavai_extras="{}"
model_info="{}"
return="no"

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
    --litellm_kalavai_extras=*)
      litellm_kalavai_extras="${1#*=}"
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
    --api_key=*)
      api_key="${1#*=}"
      ;;
    --job_id=*)
      job_id="${1#*=}"
      ;;
    --model_info=*)
      model_info="${1#*=}"
      ;;
    --return=*)
      return="yes"
      ;;
    *)
      printf "*****************************************\n"
      printf "* register_model.sh: Invalid argument: $1\n"
      printf "*****************************************\n"
      exit 1
  esac
  shift
done

echo "Registering model with LiteLLM: "$litellm_model_name

echo "----------------------------------------"
echo "LiteLLM Base URL: "$litellm_base_url
echo "LiteLLM Key: "$litellm_key
echo "LiteLLM Model Name: "$litellm_model_name
echo "LiteLLM Kalavai Extras: "$litellm_kalavai_extras
echo "Model Info: "$model_info
echo "Job ID: "$job_id
echo "----------------------------------------"


json_payload=$(cat <<EOF
{
  "model_name": "$litellm_model_name",
  "model_info": $model_info,
  "litellm_params": {
    "drop_params": false,
    "model": "$provider/$model_id",
    "api_base": "$api_base",
    "api_key": "$api_key",
    "job_id": "$job_id",
    "extras": $litellm_kalavai_extras
  }
}
EOF
)

echo "JSON payload: "$json_payload
result=$(curl -X POST "$litellm_base_url/model/new" \
  -H "Authorization: Bearer $litellm_key" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "$json_payload" 2>&1)

# result=$(curl -X POST "$litellm_base_url/model/new" \
#     -H 'Authorization: Bearer '$litellm_key \
#     -H "accept: application/json" \
#     -H "Content-Type: application/json" \
#     -d '{
#           "model_name": "'$litellm_model_name'",
#           "model_info": '$model_info',
#           "kalavai_extras": '$litellm_kalavai_extras',
#           "litellm_params": {"drop_params": false, "model": "'$provider'/'$model_id'", "api_base": "'$api_base'", "api_key": "'$api_key'", "job_id": "'$job_id'"}
#         }' 2>&1)


if [[ $? -ne 0 ]]; then
    echo $result
    exit 1
else
    echo "Model registered successfully!"
    echo $result
    if [ "$return" = "no" ]; then
      tail -f /dev/null
    fi
fi
