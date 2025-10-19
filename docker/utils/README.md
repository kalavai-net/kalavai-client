# Base python image

It includes utils

Test:

sh register_model.sh --litellm_base_url=http://localhost:31519 \
    --litellm_key=sk-1234 \
    --litellm_model_name=free/TEST \
    --model_id=Mistral-Nemo-Instruct-2407 \
    --provider=hosted_vllm \
    --api_base=http://localhost:8000 \
    --model_info='{"access_groups": ["base"]}' \
    --job_id=1234
  

Create key with access group:

curl --location 'http://localhost:31519/key/generate' \
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