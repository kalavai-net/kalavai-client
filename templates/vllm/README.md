# vLLM template

Deploy LLM models across multiple worker nodes using the vLLM library.

## External references

This template makes heavy use of the [vLLM library](https://docs.vllm.ai/en/latest/index.html).

## Key template variables

- `num_workers`: Number of workers per deployment (for tensor parallelism, i.e. how many pieces to divide the model into)
- `model_id`: Huggingface model id to load from [Huggingface](https://huggingface.co/models)
- `hf_token`: Huggingface token, required to load licensed model weights
- `gpus`: GPUs per single worker (final one = gpus * num_workers)

## How to use

Get default values, edit them and deploy:
```bash
kalavai job defaults vllm > values.yaml
# edit values.yaml as required
kalavai job run vllm --values-path values.yaml
```

Find out the url endpoint of the model with:

```bash
$ kalavai job list 

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Deployment        ┃ Status                            ┃ Endpoint               ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ vllm-deployment-1 │ Available: All replicas are ready │ http://100.8.0.2:31992 │
└───────────────────┴───────────────────────────────────┴────────────────────────┘
```

This is a model endpoint that can be interacted as you would any [LLM server](https://docs.vllm.ai/en/latest/getting_started/quickstart.html#using-openai-completions-api-with-vllm). For example:
```bash
curl http://100.8.0.2:31992/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "facebook/opt-350m",
        "prompt": "San Francisco is a",
        "max_tokens": 7,
        "temperature": 0
    }'
```

Also from python:
```python
from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://100.8.0.2:31992/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)
completion = client.completions.create(model="facebook/opt-350m",
                                      prompt="San Francisco is a")
print("Completion result:", completion)
```
