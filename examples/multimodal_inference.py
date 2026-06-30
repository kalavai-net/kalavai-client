#!/usr/bin/env python3
"""
Simple multimodal LLM inference using direct HTTP requests
Supports text and image inputs for vision language models
"""

import base64
import json
import requests
from pathlib import Path


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
        #"max_tokens": 2000,
        "temperature": 0.0,
        "repetition_penalty": 1.05,
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        }
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
    
    # Configuration
    API_URL = "https://gateway-cogenai-gateway.spaces.kalavai.net/v1" #"https://qwenvl-test-default-vllm.spaces.kalavai.net/v1"
    API_KEY = "sk-bTokNuI9f7Sa5XDxVLOcyw"
    MODEL = "inclusionAI/ZwZ-4B-FP8"
    
    print("=== Simple Multimodal Inference ===\n")
    
    # Text + Image
    script_dir = Path(__file__).parent
    image_path = script_dir / "img" / "tables.jpg"
    
    if image_path.exists():
        print("2. Image analysis:")
        content = create_multimodal_message(
            "Extract all datapoints including tables from this PDF page. Treat any empty fields as null. Return structured JSON", 
            str(image_path)
        )
        messages = [{"role": "user", "content": content}]
        
        response = chat_completion(API_URL, API_KEY, MODEL, messages)
        if response:
            result = response.json()
            print(result)


if __name__ == "__main__":
    main()
