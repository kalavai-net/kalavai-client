
from openai import OpenAI

API_URL = "https://gateway-api-shadow-gateway.spaces.kalavai.net"
MODEL = "qwant/Qwen3.6-35B-A3B-int4-mixed-AutoRound"
API_KEY = ""

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