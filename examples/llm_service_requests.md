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


## High-Performance notes


- **Streaming**: Use `stream=True` for real-time response generation
- **Batching**: Use async/await patterns for concurrent requests
- **Error Handling**: Always include proper error handling for network requests
