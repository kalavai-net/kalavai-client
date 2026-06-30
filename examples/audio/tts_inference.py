"""
TTS inference example

Model for the task: Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice

Requires:

pip install openai requests
"""
import time

from openai import OpenAI


API_URL = "https://gateway-cogenai-gateway.spaces.kalavai.net"
API_KEY = ""
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"


# Generate speech with style
client = OpenAI(base_url=f"{API_URL}/v1", api_key=API_KEY)

t = time.time()
response = client.audio.speech.create(
    model=MODEL_ID,
    voice="Vivian",
    input="Hello, this is a test of the TTS system. What if the text is longer? Does the inference time worsen? Worst? OK, I got it now.",
    instructions="Speak with great enthusiasm and energy.",
)
print(f"Inference time: {time.time() - t}")
response.stream_to_file("output.wav")

print("Output saved to output.wav")