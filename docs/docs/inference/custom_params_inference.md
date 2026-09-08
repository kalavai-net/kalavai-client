---
tags:
  - Cogenai
  - custom parameters
  - openai compatible API
---


CoGenAI is fully OpenAI compatible, meaning you can use the same code to interact with the LLM service as you would with the OpenAI API. This means that you can use the same code to interact with the service as you would with the OpenAI API, including methods and parameters to customise your inference calls.

For a detailed view of the OpenAI compatible API, supported methods and parameters, see the [LiteLLM API Documentation](https://litellm-api.up.railway.app/#/chat%2Fcompletions/chat_completion_v1_chat_completions_post).

## Example

This example shows how to make inference requests to a text-to-text model using CoGen AI service and passing custom parameters to configure the inference.

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


## Examples

### Custom parameters

Some models support custom parameters that can be passed in the `extra_body` field. For example, the Qwen model supports the `enable_thinking` parameter to disable reasoning mode.

```python

from openai import OpenAI

API_URL = "https://cogenai-prod.spaces.klalavai.net/v1"
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

