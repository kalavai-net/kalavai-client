from openai import OpenAI


API_URL = "https://gateway-api-tocalabs-gateway.spaces.kalavai.net/v1" #"https://testme-default-litellm.spaces.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1"  # Replace with your OpenAI-compatible API URL
API_KEY = "sk-oogceI1OhKObizmkyVKt3w"  # Replace with your actual API key
MODEL = "openai/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf" #"Hastagaras/Jamet-8B-L3-MK.V-Blackroot" #mistralai/Mistral-Nemo-Instruct-2407"  # Replace with your model name


# point this to your vLLM API server
client = OpenAI(
    base_url=API_URL,  # change if your server runs elsewhere
    api_key=API_KEY  # vLLM ignores the key, but the client requires it
)

def stream_chat():
    response = client.chat.completions.create(
        model=MODEL,   # replace with your model name
        messages=[{"role": "user", "content": "Tell me a long story"}],
        stream=True,
        max_tokens=500
    )

    print("Assistant:", end=" ", flush=True)
    for chunk in response:
        # Each chunk may contain part of the message
        delta = chunk.choices[0].delta
        if delta and hasattr(delta, "content") and delta.content is not None:
            print(delta.content, end="", flush=True)
        # for reasoning models
        if delta and hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
            print(delta.reasoning_content, end="", flush=True)

    print("\n--- Done ---")

if __name__ == "__main__":
    stream_chat()