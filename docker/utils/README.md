# Base python image

It includes utils

Test:

sh register_model.sh --litellm_base_url=https://api.cogenai.kalavai.net \
    --litellm_key=somekey \
    --litellm_model_name=TEST \
    --model_id=test_model \
    --provider=hosted_vllm \
    --api_base=http://localhost:0000 \
    --model_info='{"access_groups": ["free"]}' \
    --job_id=1234

TEST inference

curl -X POST 'https://api.cogenai.kalavai.net/v1/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer somekey' \
  -d '{
    "model": "TEST",
    "prompt": "What is the meaning of life?",
    "max_tokens": 1000
  }' 