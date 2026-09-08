---
tags:
  - Cogenai
  - custom parameters
  - openai compatible API
---


CoGenAI is fully OpenAI compatible, and as such you get response metrics such as token usage, latency, and other useful information in the request response body. Depending on whether you are doing streaming or non-streaming requests, the metrics will be available in different ways.

## Example

This example shows how to fetch response metrics for streaming and non-streaming requests, using the `openai` package.


## Installation

Install the required packages:

```bash
pip install openai
```

## Configuration

Substitute the following values with your own:

- `MODEL`: The model ID of the model you want to use. Example: `Qwen/Qwen3-4B`
- `API_KEY`: Your API key
- `API_URL`: The URL of the API. For CoGen AI inference, use: `https://cogenai-prod.spaces.klalavai.net/v1`


## Metrics values


Here's how to fetch the metrics:

```python
import os
from openai import OpenAI


API_KEY = "dummy"
API_URL = "https://qwen3-6-35b-a3b-7a3a14-shadow-vllm.spaces.kalavai.net/v1"
MODEL_ID = "Intel/Qwen3.6-35B-A3B-int4-mixed-AutoRound"


# Initialize the client pointing to your local or remote vLLM server
client = OpenAI(
    base_url=API_URL,
    api_key=API_KEY  # vLLM usually doesn't require one by default
)

model_name = MODEL_ID # Replace with your exact model string

# ----------------------------------------------------------------------
# 1. Standard (Non-Streaming) Request
# ----------------------------------------------------------------------
print("--- Testing Standard Request ---")

response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "user", "content": "Explain gravity in one sentence."}
    ]
)

# Extracting the response text
print(f"AI: {response.choices[0].message.content}\n")

# Extracting the metrics
if response.usage:
    print(f"📊 Metrics:")
    print(f"   Prompt Tokens:     {response.usage.prompt_tokens}")
    print(f"   Completion Tokens: {response.usage.completion_tokens}")
    print(f"   Total Tokens:      {response.usage.total_tokens}")
else:
    print("❌ No usage metrics returned.")


print("\n" + "="*40 + "\n")


# ----------------------------------------------------------------------
# 2. Streaming Request (with metrics enabled)
# ----------------------------------------------------------------------
print("--- Testing Streaming Request ---")

stream = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "user", "content": "Count from 1 to 5."}
    ],
    stream=True,
    # CRITICAL: This tells vLLM to append a final chunk containing token usage
    stream_options={"include_usage": True} 
)

print("AI: ", end="")
for chunk in stream:
    # Print tokens as they arrive
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    
    # The last chunk (or chunks) will contain the usage stats and no choices
    if chunk.usage:
        print("\n\n📊 Final Streaming Metrics:")
        print(f"   Prompt Tokens:     {chunk.usage.prompt_tokens}")
        print(f"   Completion Tokens: {chunk.usage.completion_tokens}")
        print(f"   Total Tokens:      {chunk.usage.total_tokens}")
```

