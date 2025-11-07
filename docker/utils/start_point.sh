#!/bin/bash

litellm_kalavai_extras="{}"
litellm_access_group=""
model_api_base=""
rpm_limit="50000"

while [ $# -gt 0 ]; do
  case "$1" in
    --litellm_access_group=*)
      litellm_access_group="${1#*=}"
      ;;
    --litellm_kalavai_extras=*)
      litellm_kalavai_extras="${1#*=}"
      ;;
    --model_api_base=*)
      model_api_base="${1#*=}"
      ;;
    --rpm_limit=*)
      rpm_limit="${1#*=}"
      ;;
    *)
      printf "**************************************\n"
      printf "* start_point.sh: Invalid argument: $1\n"
      printf "**************************************\n"
      exit 1
  esac
  shift
done

if [ -z "$litellm_access_group" ];
then
  litellm_access_group_str="{}"
else
  litellm_access_group_str="{\"access_groups\": [\"${litellm_access_group}\"]}"
fi
if [ -z "$model_api_base" ];
then
  model_api_base=$MODEL_API_BASE
fi

echo ">>> Creating new entry on LiteLLM"

echo "----------------------------------------"
echo "Raw litellm_access_group: "$litellm_access_group
echo "LiteLLM Kalavai Extras: "$litellm_kalavai_extras
echo "LiteLLM Access Group: "$litellm_access_group_str
echo "Model ID: "$MODEL_ID
echo "LiteLLM model name: "$LITELLM_MODEL_NAME
echo "Provider: "$PROVIDER
echo "Model API Base: "$model_api_base
echo "Deployment ID: "$DEPLOYMENT_ID
echo "----------------------------------------"

# Register the model with LiteLLM
/workspace/register_model.sh \
    --litellm_base_url=$LITELLM_BASE_URL \
    --litellm_key=$LITELLM_KEY \
    --litellm_model_name="$LITELLM_MODEL_NAME" \
    --model_id=$MODEL_ID \
    --provider=$PROVIDER \
    --api_base=$model_api_base \
    --litellm_kalavai_extras="$litellm_kalavai_extras" \
    --model_info="$litellm_access_group_str" \
    --job_id=$DEPLOYMENT_ID \
    --rpm_limit=$rpm_limit

# Start the Lago event submitter (for billing)
#{% if lago_url != "" %}--return=1 \{% endif %}
# {% if lago_url != "" %}
# python event_generator.py \
#   --lago_url={{lago_url}} \
#   --api_key={{lago_api_key}} \
#   --external_subscription_id={{lago_external_subscription_id}} \
#   --event_code={{lago_event_code}} \
#   --interval={{lago_event_interval}} \
#   --verbose
# {% endif %}