from openai import OpenAI

import time

API_URL = "http://100.97.111.1:30960/v1" # Replace with your OpenAI-compatible API URL
API_KEY = "dummy"  # Replace with your actual API key
MODEL = "Qwen/Qwen3.5-0.8B"  # Replace with your model name


# point this to your vLLM API server
client = OpenAI(
    base_url=API_URL,  # change if your server runs elsewhere
    api_key=API_KEY  # vLLM ignores the key, but the client requires it
)

def stream_chat():
    t = time.time()
    response = client.chat.completions.create(
        model=MODEL,   # replace with your model name
        messages=[{"role": "user", "content": "Tell me a story"}],
        stream=True,
        max_tokens=500
    )
    print(f"Time to first token: {time.time() - t}")

    print("Assistant:", end=" ", flush=True)
    for chunk in response:
        # Each chunk may contain part of the message
        delta = chunk.choices[0].delta
        if delta and hasattr(delta, "content") and delta.content is not None:
            print(delta.content, end="", flush=True)
        # for reasoning models
        if delta and hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
            print(delta.reasoning_content, end="", flush=True)
        if delta and hasattr(delta, "reasoning") and delta.reasoning is not None:
            print(delta.reasoning, end="", flush=True)

    print("\n--- Done ---")

if __name__ == "__main__":
    stream_chat()