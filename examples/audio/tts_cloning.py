"""
TTS Cloning Example

Model for the task: Qwen/Qwen3-TTS-12Hz-1.7B-Base
"""
import requests
import json


API_URL = "https://qwen-tts-test-default-vllm.spaces.kalavai.net"
API_KEY = "dummy"
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
REFERENCE_AUDIO = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-ASR-Repo/asr_en.wav"
REFERENCE_TEXT = "Uh huh. Oh yeah, yeah. He wasn't even that big when I started listening to him, but and his solo music didn't do overly well, but he did very well when he started writing for other people"


def clone_voice():
    url = f"{API_URL}/v1/audio/speech"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": MODEL_ID,
        "input": "Hello, this is a cloned voice",
        "task_type": "Base",
        "ref_audio": REFERENCE_AUDIO,
        "ref_text": REFERENCE_TEXT
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        with open("cloned.wav", "wb") as f:
            f.write(response.content)
        
        print("Voice cloned successfully! Saved as cloned.wav")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clone_voice()