#!/bin/bash

echo "Deleting model: $DEPLOYMENT_ID";

response=$(python3 /workspace/delete_model.py \
    --litellm_url=$LITELLM_BASE_URL \
    --api_key=$LITELLM_KEY \
    --job_id=$DEPLOYMENT_ID);


# curl -X POST "$LITELLM_BASE_URL/model/delete" \
#     -H "Authorization: Bearer $LITELLM_KEY" \
#     -H "accept: application/json" \
#     -H "Content-Type: application/json" \
#     -d '{ "id": "'$model_id'"}';