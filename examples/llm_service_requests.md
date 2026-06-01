---
tags:
  - LLM
  - openai compatible API
---

> Work In progress

# LLM Service Requests Example

This example shows how to make requests to the LLM service using the OpenAI compatible API.

## Installation

Install the required packages:

```bash
pip install openai
```

## Configuration

Substitute the following values with your own:

- `MODEL`: The model ID of the model you want to use. Example: `Qwen/Qwen3-4B`
- `API_KEY`: Your API key (if authentication is required)
- `API_URL`: The URL of the API. Example: `http://kalavai-api.public.kalavai.net/v1`

## Examples

### 1. Streaming Inference

A single request with streaming response to get the output tokens as soon as they are generated.


```python
from openai import OpenAI

API_URL = "http://kalavai-api.public.kalavai.net/v1"
API_KEY = "<your-api-key>"
MODEL = "Qwen/Qwen3-4B"

client = OpenAI(
    base_url=API_URL,
    api_key=API_KEY
)

def stream_chat():
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Tell me a long story"}],
        stream=True
    )

    print("Assistant:", end=" ", flush=True)
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            print(delta.content, end="", flush=True)

    print("\n--- Done ---")

if __name__ == "__main__":
    stream_chat()
```


### 2. Batched Inference

Multiple requests submitted simultaneously. The results are displayed in bulk once all of them are completed.


```python
from openai import OpenAI
import asyncio

API_URL = "http://kalavai-api.public.kalavai.net/v1"
API_KEY = "<your-api-key>"
MODEL = "Qwen/Qwen3-4B"

client = OpenAI(
    base_url=API_URL,
    api_key=API_KEY
)

async def batched_inference_openai():
    prompts = [
        "What is the capital of France?",
        "Explain quantum computing",
        "Write a short poem",
        "What are the benefits of exercise?",
        "Describe the solar system"
    ]
    
    tasks = []
    for i, prompt in enumerate(prompts):
        task = asyncio.create_task(single_request(client, MODEL, prompt, i))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print(f"Response {i+1}: {result[:100]}...")

async def single_request(client, model, prompt, request_id):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    asyncio.run(batched_inference_openai())
```

## Custom parameters

Some models support custom parameters that can be passed in the `extra_body` field. For example, the Qwen model supports the `enable_thinking` parameter to disable reasoning mode.

```python

from openai import OpenAI

API_URL = "http://kalavai-api.public.kalavai.net/v1"
API_KEY = "<your-api-key>"
MODEL = "Qwen/Qwen3-4B"

client = OpenAI(
    base_url=API_URL,
    api_key=API_KEY
)

def stream_chat():
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Who, Tell me a story"}],
        stream=True,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        }
    )

    for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            print(delta.content, end="", flush=True)
        if delta and hasattr(delta, 'reasoning_content') and delta.reasoning_content:
            print(delta.reasoning_content, end="", flush=True)
        if delta and hasattr(delta, 'reasoning') and delta.reasoning:
            print(delta.reasoning, end="", flush=True)

    print("\n--- Done ---")

if __name__ == "__main__":
    stream_chat()
```

## OpenAI compatible API

With the OpenAI compatible API, you can use the same code to interact with the LLM service as you would with the OpenAI API. This means that you can use the same code to interact with the service as you would with the OpenAI API, including methods and parameters to customise your inference calls.

For a detailed view of the OpenAI compatible API, supported methods and parameters, see the [LiteLLM API Documentation](https://litellm-api.up.railway.app/#/chat%2Fcompletions/chat_completion_v1_chat_completions_post).


## High-Performance notes


- **Streaming**: Use `stream=True` for real-time response generation
- **Batching**: Use async/await patterns for concurrent requests
- **Error Handling**: Always include proper error handling for network requests
