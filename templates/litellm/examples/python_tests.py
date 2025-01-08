"""Example on how to interact with the LiteLLM endpoint"""

import requests

LITELLM_URL = "http://206.189.19.245:30916"
LITELLM_KEY = "sk-qoQC5lijoaBwXoyi_YP1xA"
MODEL_NAME = ""

def list_models():
    response = requests.get(
        f"{LITELLM_URL}/v1/models",
        headers={"Authorization": f"Bearer {LITELLM_KEY}"}
    )
    return response.json()

def model_inference():
    response = requests.post(
        f"{LITELLM_URL}/chat/completions",
        headers={"Authorization": f"Bearer {LITELLM_KEY}"},
        json={
            "model": MODEL_NAME,
            "messages": [
            {
                "role": "user",
                "content": "what llm are you"
            }]
        }
    )
    return response.json()


if __name__ == "__main__":
    print(
        list_models()
    )
