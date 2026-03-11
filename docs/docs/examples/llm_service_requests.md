---
tags:
  - LLM
  - openai compatible API
---

> Work In progress

# LLM Service Requests Example

This example shows how to make requests to the LLM service using the OpenAI compatible API.

Requires to have `openai` installed:

```bash
pip install openai
```


Substitute the following values with your own:

- `MODEL`: The model ID of the model you want to use. Example: `Qwen/Qwen3-4B`
- `API_KEY`: Your API key (if authentication is required)
- `API_URL`: The URL of the API. Example: `http://kalavai-api.public.kalavai.net/v1`



```python
from openai import OpenAI


API_URL = "http://51.159.173.70:31567/v1" #"https://api.cogenai.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1"  # Replace with your OpenAI-compatible API URL
API_KEY = ""  # Replace with your actual API key
MODEL = "Qwen/Qwen3-4B" # Replace with your model name


# point this to your vLLM API server
client = OpenAI(
    base_url=API_URL,  # change if your server runs elsewhere
    api_key=API_KEY  # vLLM ignores the key, but the client requires it
)

def stream_chat():
    response = client.chat.completions.create(
        model=MODEL,   # replace with your model name
        messages=[{"role": "user", "content": "Tell me a long story"}],
        stream=True
    )

    print("Assistant:", end=" ", flush=True)
    for chunk in response:
        # Each chunk may contain part of the message
        delta = chunk.choices[0].delta
        if delta and delta.content:
            print(delta.content, end="", flush=True)

    print("\n--- Done ---")

if __name__ == "__main__":
    stream_chat()
```

