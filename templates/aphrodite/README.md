# Aphrodite engine template

Deploy LLM models across multiple worker nodes using the `Aphrodite Engine`, including quantized versions.

## External references

This template makes heavy use of the [Aphrodite Engine](https://aphrodite.pygmalion.chat/).

List of supported model architectures [here](https://aphrodite.pygmalion.chat/pages/usage/models.html).


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

┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Deployment  ┃ Status                            ┃ Workers    ┃ Endpoint                   ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ aphrodite-1 │ Available: All replicas are ready │ Running: 1 │ http://192.168.68.67:31685 │
└─────────────┴───────────────────────────────────┴────────────┴────────────────────────────┘
```

This is a model endpoint that can be interacted as you would any [LLM server](https://aphrodite.pygmalion.chat/pages/usage/openai.html). For example:
```bash
curl http://192.168.68.67:31685/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "facebook/opt-350m",
        "prompt": "Every age it seems is tainted by the greed of men. Rubbish to one such as I,",
        "max_tokens": 100,
        "temperature": 0
    }'
```

Also from python:
```python
from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://192.168.68.67:31685/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)
completion = client.completions.create(model="facebook/opt-350m",
                                      prompt="San Francisco is a")
print("Completion result:", completion)
```

## Examples

Check out [example](examples/) `values.yaml` ready for deployment
- [facebook/OPT-350m](examples/opt-350m.yaml)
