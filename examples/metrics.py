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