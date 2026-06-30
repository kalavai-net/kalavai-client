"""
Voice Design inference example

Model for the task: Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign

"""

import requests
import json

API_URL = "https://audio-test-default-vllm.spaces.kalavai.net"
API_KEY = "dummy"
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

