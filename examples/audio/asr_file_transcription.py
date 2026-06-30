"""
ASR inference example (streaming=False)

Requires:

pip install httpx openai
"""

import httpx
from openai import OpenAI
import time

MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
API_URL = "https://gateway-cogenai-gateway.spaces.kalavai.net"
API_KEY = ""


# Initialize client
client = OpenAI(
    base_url=f"{API_URL}/v1",
    api_key=API_KEY
)
audio_url = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-ASR-Repo/asr_en.wav"
audio_file = httpx.get(audio_url).content

t = time.time()
transcription = client.audio.transcriptions.create(
    model=MODEL_ID,
    file=audio_file,
)

print(f"Transcription: {transcription.text}")
print(f"Time: {time.time() - t}")