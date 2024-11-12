# Aphrodite engine template

Deploy LLM models across multiple worker nodes using the `Aphrodite Engine`, including quantized versions.

## External references

This template makes heavy use of the [Aphrodite Engine](https://aphrodite.pygmalion.chat/).

List of supported model architectures [here](https://aphrodite.pygmalion.chat/pages/usage/models.html).

**Important**: when deploying LLMs from Huggingface, make sure the model architecture is supported by aphrodite-engine. There are well known issues ([#786](https://github.com/PygmalionAI/aphrodite-engine/issues/786), [#781](https://github.com/PygmalionAI/aphrodite-engine/issues/781), [#773](https://github.com/PygmalionAI/aphrodite-engine/issues/773)) with certain models.


## Key template variables

- `storage`: Pool storage to use to cache model weights. Useful to persist weights across jobs. Pools have a default storage named `pool-cache`, and you can create new ones with `kalavai storage create <name> <capacity>`.
- `num_workers`: Number of workers per deployment (for tensor parallelism, i.e. how many pieces to divide the model into)
- `repo_id`: Huggingface repository to load from [Huggingface](https://huggingface.co/models). This usually takes the form of `OrgName/ModelID`
- `filename` (optional): if a repo contains multiple versions of a model, one can explicitly define which file to fetch. This is useful when downloading a GGUF model. Only the filename is requred (e.g. `Llama-3.1-8B-Lexi-Uncensored_V2_F16.gguf` on repository [Orenguteng/Llama-3.1-8B-Lexi-Uncensored-V2-GGUF](https://huggingface.co/Orenguteng/Llama-3.1-8B-Lexi-Uncensored-V2-GGUF/tree/main))
- `hf_token` (optional): Huggingface token, required to load licensed model weights
- `gpus`: GPUs per single worker (final one = gpus * num_workers)
- `gpu_vram`: Minimum vRAM for each GPU requested (total one = gpus * num_workers * gpu_vram)
- `extra` (optional): any extra parameters to pass to aphrodite engine. Expected format: `--parameter1_name parameter1_value --parameterX_name parameterX_value`
- `tensor_parallel_size`: Tensor parallelism (use the number of GPUs per node)
- `pipeline_parallel_size`: Pipeline parallelism (use the number of nodes)


## How to use

Get default values, edit them and deploy:
```bash
kalavai job defaults aphrodite > values.yaml
# edit values.yaml as required
kalavai job run aphrodite --values-path values.yaml
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
curl 192.168.68.67:31685/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
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
completion = client.completions.create(model="qwen2.5-0.5B.yaml",
                                      prompt="San Francisco is a")
print("Completion result:", completion)
```

## Examples

Check out [example](examples/) `values.yaml` ready for deployment
- [qwen2.5-0.5B.yaml](examples/qwen2.5-0.5B.yaml)
