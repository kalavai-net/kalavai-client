---
tags:
  - stable diffusion
  - image generation
  - text2image
---

> Work In progress

# Image Generation Example

This example shows how to generate images using the Stable diffusion template.

Substitute the following values with your own:

- `model_id`: The model ID of the model you want to use. Example: `black-forest-labs/FLUX.2-klein-4B`
- `API_KEY`: Your API key (if authentication is required)
- `API_URL`: The URL of the API. Example: `http://kalavai-api.public.kalavai.net:31311/v1/images/generations`


```python
import time
import requests
import base64

t = time.time()
MODEL_ID = "<your-model-id>"
API_URL = "<your-api-url>"
API_KEY = "<your-api-key>"

prompt = "a realistic picture of a sunset."
resp = requests.post(
    API_URL,
    headers={
        "Authorization": f"Bearer {API_KEY}"
    },
    json={
        "prompt": prompt,
        "model": MODEL_ID,
        "n": 1,
        "size": "256x256", # only 256x256, 512x512, 1024x1024 are supported
        "response_format": "b64_json",
        "extra": {"num_inference_steps": 5} # supported parameters https://huggingface.co/docs/diffusers/api/pipelines/flux#diffusers.FluxPipeline
    },
)
print(f"Inference time: {time.time()-t:.2f}s")

# Debug: Print the response structure
print("Response status:", resp.status_code)

for i in range(len(resp.json()["data"])):
    image_data = resp.json()["data"][i].get("b64_json")
    if image_data is None:
        print(f"Warning: No b64_json data found for image {i}")
        print(f"Available keys: {list(resp.json()['data'][i].keys())}")
        continue
    
    with open(f"output_{i}.png", 'wb') as f:
        f.write(base64.b64decode(image_data))
```

## Batched Inference Example

This example demonstrates batched inference with multiple images and batch size optimization.

```python
import time
import requests
import base64

t = time.time()
MODEL_ID = "<your-model-id>"
API_URL = "<your-api-url>"
API_KEY = "<your-api-key>"

resp = requests.post(
    API_URL,
    headers={
        "Authorization": f"Bearer {API_KEY}"
    },
    json={
        "prompt": "a majestic mountain landscape with snow peaks.", 
        "model": MODEL_ID,
        "n": 2,  # Generate 2 images per prompt
        "batch_size": 2,  # Process in batches of 2 for efficiency
        "size": "256x256",
        "response_format": "b64_json",
        "extra": {"num_inference_steps": 5}
)
print(f"Batched inference time: {time.time()-t:.2f}s")

# Debug: Print the response structure
print("Response status:", resp.status_code)
print(f"Total images generated: {len(resp.json()['data'])}")

for i in range(len(resp.json()["data"])):
    image_data = resp.json()["data"][i].get("b64_json")
    if image_data is None:
        print(f"Warning: No b64_json data found for image {i}")
        print(f"Available keys: {list(resp.json()['data'][i].keys())}")
        continue
    
    with open(f"batched_output_{i}.png", 'wb') as f:
        f.write(base64.b64decode(image_data))
```

