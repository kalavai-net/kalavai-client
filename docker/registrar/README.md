# Registrar utils

Utils container mostly for model registration on gateway:

- Manages registration / deregistration of models in external Gateway (LiteLLM)
- Utils scripts for connectivity between workers / servers
- Handles billing and tracking heartbeats


## Model registration

The registrar container can be used to register models in the gateway. It will call the gateway API to register the model.

### Env variables

Functionality is configured via environment variables:

- `MODEL_ID`: model id matching the id in the MODEL_API_BASE service
- `MODEL_API_BASE`: internal address for the OpenAI compatible API server where the model is accessible
- `LITELLM_BASE_URL`: internal address for the gateway service
- `LITELLM_API_KEY`: api key to grant access to the gateway service
- `LITELLM_MODEL_NAME`: new model id reference for the model in the gateway API
- `LITELLM_EXTRAS`: string dictionary with extra info
- `LITELLM_ACCESS_GROUP`: access group to assign the model to in gateway
- `PROVIDER`: gateway provider
- `DEPLOYMENT_ID`: internal id to link the model to a deployment ID in Kalavai


## Billing heartbeat

The registrar container can be used to send billing heartbeats to track model usage. It will call the gateway API to send a heartbeat with the current usage metrics.

### Env variables

Functionality is configured via environment variables:

- `USER_ID`: user id to track the usage
- `JOB_ID`: job id to track the usage
- `VRAM_USAGE`: VRAM usage in GB
- `MEMORY_USAGE`: Memory usage in GB
- `CPU_USAGE`: CPU usage in percentage
- `GPU_TYPE`: GPU type
- `INTERVAL_SECONDS`: interval in seconds to send the heartbeat
- `PROVIDER`: gateway provider


## Build

```bash
docker build -t ghcr.io/kalavai-net/kalavai-registrar:latest .
docker push ghcr.io/kalavai-net/kalavai-registrar:latest
```

## Notes

It includes utils

Test:

sh register_model.sh --litellm_base_url=http://localhost:32415 \
    --litellm_key=sk-1234 \
    --litellm_model_name=free/user \
    --model_id=Mistral-Nemo-Instruct-2407 \
    --provider=hosted_vllm \
    --api_base=http://localhost:8000 \
    --model_info='{"access_groups": ["user"]}' \
    --job_id=1234
  

Create key with access group:

curl --location 'http://localhost:32415/key/generate' \
-H 'Authorization: Bearer sk-1234' \
-H 'Content-Type: application/json' \
-d '{"models": ["base"]}'

base: sk-HOUEz9Ys9fzqypXTu-KBRQ
Paid: sk-1023r4Z5RnOf0pE5U2IuHQ

TEST inference

curl -X POST 'http://localhost:31519/v1/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-HOUEz9Ys9fzqypXTu-KBRQ' \
  -d '{
    "model": "free/TEST",
    "prompt": "What is the meaning of life?",
    "max_tokens": 1000
  }' 


Testing get litellm model:

python get_litellm_id.py --litellm_url=http://51.159.190.138:31236 \
  --api_key=sk-1234 \
  --job_id=aad25d2f-b24c-42c2-8a2a-2b2df1ec8bbf-free-model1 \
  --model_name=free/model1