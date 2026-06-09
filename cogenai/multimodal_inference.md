---
tags:
  - Cogenai
  - multimodal
  - image
---

> Work In progress

# Multimodal Inference Example

This example shows how to make requests to the multimodal inference service using CoGen AI API.

## Installation

Install the required packages:

```bash
pip install requests
```

## Configuration

Substitute the following values with your own:

- `MODEL`: The model ID of the multimodal model you want to use. Example: `unsloth/NVIDIA-Nemotron-3-Nano-Omni-30B-A3B-Reasoning-Q4_K_M`
- `API_KEY`: Your API key (if authentication is required)
- `API_URL`: The URL of the API. For CoGen AI inference, use: `https://cogenai-prod.spaces.klalavai.net/v1`


## Examples

### Single inference request

A single request containing an image and text:


```python
import base64
import requests
from pathlib import Path

# Configuration
API_URL = "https://cogenai-prod.spaces.klalavai.net/v1"
API_KEY = "<api key>"
MODEL = "unsloth/NVIDIA-Nemotron-3-Nano-Omni-30B-A3B-Reasoning-Q4_K_M"



def encode_image(image_path):
    """Encode image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_image_mime_type(image_path):
    """Get MIME type for image file"""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg', 
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def create_multimodal_message(text_prompt, image_path=None):
    """Create message with text and optional image"""
    content = [{"type": "text", "text": text_prompt}]
    
    if image_path:
        base64_image = encode_image(image_path)
        mime_type = get_image_mime_type(image_path)
        
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_image}"
            }
        })
    
    return content


def chat_completion(api_url, api_key, model, messages, stream=False):
    """Send chat completion request to API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{api_url}/chat/completions",
            headers=headers,
            json=data,
            stream=stream
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def main():
    """Simple multimodal inference examples"""
    
    print("=== Simple Multimodal Inference ===\n")
    
    # Text + Image
    script_dir = Path(__file__).parent
    image_path = script_dir / "img" / "job_progress.png"
    
    if image_path.exists():
        print("2. Image analysis:")
        content = create_multimodal_message(
            "What does this image show?", 
            str(image_path)
        )
        messages = [{"role": "user", "content": content}]
        
        response = chat_completion(API_URL, API_KEY, MODEL, messages)
        if response:
            result = response.json()
            print(result)


if __name__ == "__main__":
    main()

```

