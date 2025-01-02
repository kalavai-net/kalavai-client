#!/bin/bash
# Test LiteLLM API
MODEL_NAME="qwen-qwen2-5-0-5b-instruct"
MODEL_ID="2fc88960-6dc9-439c-a5ae-6363aa65306b"
MASTER_KEY="sk-06EkGxEJS6_cHS_C1QE1nA"
LITELLM_URL="http://192.168.68.67:31471"
LLM_API_BASE="http://vllm-1:8080"

subcommand=$1
case "$subcommand" in
    inference)
        curl --location $LITELLM_URL'/chat/completions' \
            --header 'Authorization: Bearer '$MASTER_KEY \
            --header 'Content-Type: application/json' \
            --data '{
                "model": "'$MODEL_NAME'",
                "messages": [
                    {
                    "role": "user",
                    "content": "what llm are you"
                    }
                ]
            }'
        ;;
    new)
        API_BASE="${LLM_API_BASE}/v1"
        extra='{ "extra": "--dtype float16"}'
        curl -X POST "$LITELLM_URL/model/new" \
            -H 'Authorization: Bearer '$MASTER_KEY \
            -H "accept: application/json" \
            -H "Content-Type: application/json" \
            --data '{
                "model_name": "'$MODEL_NAME'",
                "model_info": '"$extra"',
                "litellm_params": {
                    "model": "hosted_vllm/'$MODEL_NAME'", "api_base": "'$API_BASE'"
                }
            }'
        ;;
    list)
        curl -X GET "$LITELLM_URL/v1/models" \
            -H 'Authorization: Bearer '$MASTER_KEY \
            -H "accept: application/json" \
            -H "Content-Type: application/json"
        ;;
    delete)
        MODEL_ID=$(python ../../docker/utils/get_litellm_id.py \
                    --litellm_url=$LITELLM_URL \
                    --api_key=$MASTER_KEY \
                    --model_name=$MODEL_NAME)
        echo "Deleting model "$MODEL_ID
        curl -X POST "$LITELLM_URL/model/delete" \
            -H 'Authorization: Bearer '$MASTER_KEY \
            -H "accept: application/json" \
            -H "Content-Type: application/json" \
            -d '{ "id": "'$MODEL_ID'"}'
        ;;
esac
