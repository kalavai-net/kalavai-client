---
tags:
  - audio
  - text-to-speech
  - openai compatible API
---


# Text-to-Speech Inference Example

This example shows how to make requests to the TTS service using the OpenAI compatible API.

## Installation

Install the required packages:

```bash
pip install openai requests
```

## Configuration

Substitute the following values with your own:

- `MODEL`: The TTS-enabled model ID of the model you want to use. Example: `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`
- `API_KEY`: Your API key
- `API_URL`: The URL of the API. For CoGen AI inference, use: `https://cogenai-prod.spaces.klalavai.net/v1`


## Examples

### 1. Text-to-speech Inference

A single request to generate speech from text, with an option to add instructions for the voice style.


```python
import time

from openai import OpenAI


API_URL = "https://cogenai-prod.spaces.klalavai.net/v1"
API_KEY = "<your key>"
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
```

For more examples on CustomVoice, check the [vLLM CustomVoice guide](https://docs.vllm.ai/projects/vllm-omni/en/latest/serving/speech_api/#customvoice-with-style-instruction).



### 2. Voice design Inference

A single request to design a custom voice.


```python
import requests
import json

API_URL = "https://cogenai-prod.spaces.klalavai.net/v1"
API_KEY = "<your key>"
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"


# Convert curl command to Python request
url = f"{API_URL}/v1/audio/speech"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}
data = {
    "model": MODEL_ID,
    "input": "Annie, this is great!",
    "task_type": "VoiceDesign",
    "instructions": "A warm, friendly grandma voice with a gentle tone"
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    with open("designed.wav", "wb") as f:
        f.write(response.content)
    print("Audio file saved as designed.wav")
else:
    print(f"Error: {response.status_code}")
    print(response.text)


```


For more examples on VoiceDesign, check the [vLLM VoiceDesign guide](https://docs.vllm.ai/projects/vllm-omni/en/latest/serving/speech_api/#voicedesign-natural-language-voice-description).