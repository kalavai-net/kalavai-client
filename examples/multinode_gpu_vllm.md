# Multi node GPU LLM deployment with Kalavai

## Example card

**Template**: [vLLM](../templates/vllm/README.md)

**Goal**: deploy a single Large Language Model across multiple machines and expose it via an OpenAI compatible API.


## Pre-requisites

- Install [kalavai cli](../README.md#install)
- Setup a [kalavai cluster](../README.md#cluster-quick-start) with 2 machines.
- Each machine should have at least 1 NVIDIA GPU.
- You have a HuggingFace account and a HF token
- You have been granted access to google's [gemma-2-2b](https://huggingface.co/google/gemma-2-2b) model.

## Getting started

We wish to deploy [gemma-2-2b](google/gemma-2-2b) across two GPUs, located in two different nodes.

1. (optional) On any node, fetch the default configuration for vLLM templates:
```bash
kalavai job defaults vllm > values.yaml
```

2. Edit the values.yaml file with the following:
```yaml
template_values:
- name: deployment_name
  value: vllm-gemma-1
  default: vllm-gemma-1
  description: "Name of the deployment job"
- name: replicas
  value: "1"
  default: "1"
  description: "How many replicas to deploy for the model"
- name: num_workers
  value: "2"
  default: "2"
  description: "Workers per deployment (for tensor parallelism)"
- name: model_id
  value: google/gemma-2-2b
  default: null
  description: "Huggingface model id to load"
- name: hf_token
  value: <yout token>
  default: null
  description: "Huggingface token, required to load model weights"
- name: cpus
  value: "4"
  default: "4"
  description: "CPUs per single worker (final one = cpus * num_workers)"
- name: gpus
  value: "1"
  default: "1"
  description: "GPUs per single worker (final one = gpus * num_workers)"
- name: memory
  value: "4Gi"
  default: "4Gi"
  description: "RAM memory per single worker (final one = memory * num_workers)"
- name: tensor_parallel_size
  value: "2"
  default: "1"
  description: "Tensor parallelism (use the number of GPUs per node)"
- name: pipeline_parallel_size
  value: "1"
  default: "1"
  description: "Pipeline parallelism (use the number of nodes)"
- name: shmem_size
  value: "4Gi"
  default: "4Gi"
  description: "Size of the shared memory volume"
- name: extra
  value: "--dtype float16 --enforce-eager --swap-space 0"
  default: ""
  description: "Extra parameters to pass to the vLLM server. See https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html#command-line-arguments-for-the-server"
```

3. Make sure you add your own HuggingFace token, e.g.:

```yaml
- name: hf_token
  value: <yout token>
```

4. Deploy your vLLM template:
```bash
kalavai job run vllm --values-path values.yaml
```

5. Wait until it is ready; it may take a few minutes depending on your internet connection. Monitor the deployment until status is `Available`:
```bash
$ kalavai job list

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Deployment        ┃ Status                            ┃ Endpoint               ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ vllm-gemma-1      │ Available: All replicas are ready │ http://100.8.0.2:31992 │
└───────────────────┴───────────────────────────────────┴────────────────────────┘
```

6. Now you are ready to do inference with the model! Substitute the URL below with the endpoint indicated above:

```bash
curl http://100.8.0.2:31992/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "google/gemma-2-2b",
        "prompt": "I would walk 500",
        "max_tokens": 50,
        "temperature": 0
    }'
```

7. Alternatively, you can do inference in Python:

```python
from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://100.8.0.2:31992/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)
completion = client.completions.create(
    model="google/gemma-2-2b",
    prompt="I would walk 500")
print("Completion result:", completion)
```

## Debug

If you want to inspect what's going on with the openAI server, you can access the full logs of the job (on each node) with:
```bash
kalavai job logs vllm-gemma-1
```

## Delete deployment

Once you are done with your model, you can delete the deployment with
```bash
kalavai job delete vllm-gemma-1
```