# vLLM template

Deploy LLM models across multiple worker nodes using the vLLM library. This template is designed to work with GPU workers.

## External references

This template makes heavy use of the [vLLM library](https://docs.vllm.ai/en/latest/index.html).

## Key template variables

- `workers`: Number of workers per deployment (for tensor and pipeline parallelism, i.e. how many pieces to divide the model into)
- `model_id`: Huggingface repository to load from [Huggingface](https://huggingface.co/models). This usually takes the form of `OrgName/ModelID`
- `hf_token` (optional): Huggingface token, required to load licensed model weights
- `extra` (optional): any [extra parameters](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html#cli-reference) to pass to vLLM engine. Expected format: `--parameter1_name parameter1_value --parameterX_name parameterX_value`
- `tensor_parallel_size`: Tensor parallelism (use the number of GPUs per node)
- `pipeline_parallel_size`: Pipeline parallelism (use the number of nodes)

If you have a [LiteLLM server](https://github.com/kalavai-net/kalavai-client/tree/main/templates/litellm) deployed in your pool (default for [public LLM pool](https://kalavai-net.github.io/kalavai-client/public_llm_pool/)), you can pass on the following parameters to rregister the model with it:

- `litellm_key` as the API key.
- `litellm_base_url` as the endpoint for the LiteLLM job.


## How to use

Get default values, edit them and deploy:
```bash
kalavai job defaults vllm > values.yaml
# edit values.yaml as required
kalavai job run vllm --values values.yaml
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
curl http://100.10.0.2:31992/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "prompt": "San Francisco is a",
        "max_tokens": 100,
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

## Examples

Check out the [qwen example](examples/qwen2.5-0.5B.yaml),ready for deployment.
