import requests
import json


API_URL = "https://gemma-3-27b-it-9f4352-default-llamacpp.spaces.kalavai.net/" #"https://testme-default-litellm.spaces.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1"  # Replace with your OpenAI-compatible API URL
MODEL = "openai/gemma-3-27b-it-Q4_K_M.gguf" #"Hastagaras/Jamet-8B-L3-MK.V-Blackroot" #mistralai/Mistral-Nemo-Instruct-2407"  # Replace with your model name


def generate_chat():
    """Generate a chat response using Ollama's /api/generate endpoint"""
    
    url = f"{API_URL}/api/generate"
    
    payload = {
        "model": MODEL,
        "prompt": "Tell me a long story",
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 100
        }
    }
    
    try:
        print("Assistant:", end=" ", flush=True)
        
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if data.get('response'):
                        print(data['response'], end="", flush=True)
                    
                    # Check if generation is complete
                    if data.get('done'):
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        print("\n--- Done ---")
        
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    generate_chat()
