---
tags:
  - audio
  - speech-to-text
  - asr
  - Automatic Speech Recognition
  - openai compatible API
---


# Automatic Speech Recognition Inference Example

This example shows how to make requests to the Automatic Speech Recognition (ASR) service using the OpenAI compatible API.

## Installation

Install the required packages:

```bash
pip install openai httpx
```

## Configuration

Substitute the following values with your own:

- `MODEL`: The TTS-enabled model ID of the model you want to use. Example: `Qwen/Qwen3-ASR-1.7B`
- `API_KEY`: Your API key
- `API_URL`: The URL of the API. For CoGen AI inference, use: `https://cogenai-prod.spaces.klalavai.net/v1`


## Examples

### ASR Inference

A single request to transcribe an audio file.


```python
import httpx
from openai import OpenAI
import time

MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
API_URL = "https://gateway-cogenai-gateway.spaces.kalavai.net"
API_KEY = "sk-pEF6RexG5HxrjV2lVn2aRA"


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
```

For more examples on ASR, check the [vLLM ASR guide](https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3-ASR.html).

