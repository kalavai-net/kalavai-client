---
tags:
  - petals
  - share
---

# Public Petals Swarm: BitTorrent-style LLMs

Contribute to the public Petals swarm and help deploy and fine tune Large Language Models across consumer-grade devices. See more about the Petals projecyt [here](https://github.com/bigscience-workshop/petals). You'll get:
- Eternal kudos from the community!
- Access to all the models in the server
- Easy access for inference (via Petals SDK and installation-free Kalavai endpoint).


## Requirements

- A free Kalavai account. Create one [here](https://platform.kalavai.net).
- A computer with the minimum requirements (see below)

Hardware requirements
- 1+ NVIDIA GPU
- 2+ CPUs
- 4GB+ RAM
- Free space 4x available VRAM (for an 8GB VRAM GPU, you'll need ~32GB free space in your disk)

## How to join

1. Create a [free account](https://platform.kalavai.net) with Kalavai.

2. Install the kalavai client following the instructions [here](https://kalavai-net.github.io/kalavai-client/getting_started/). Currently we support Linux distros and Windows.

3. Get the joining token. Visit our [platform](https://platform.kalavai.net) and go to `Compute pools`. Then click `Join` on the `Petals` Pool to reveal the joining details. Copy the command (including the token).

![Join Petals](/assets/images/join.png)

4. From the computer you want to share work with, run the joining command:

```bash
$ kalavai pool join <token>

[16:28:14] Token format is correct
           Joining private network

[16:28:24] Scanning for valid IPs...
           Using 100.10.0.8 address for worker
           Connecting to PETALS @ 100.10.0.9 (this may take a few minutes)...
[16:29:41] Worskpace created
           You are connected to PETALS
```

## Check Petals health

Kalavai's pool connects directly to the public swarm on Petals, which means we can use their [public health check UI](https://health.petals.dev/) to see how much we are contributing and what models are ready to use.

![alt text](/assets/images/petals_health.png)

Models with at least one copy of each shard (a green dot in each column) are ready to be used. If not, wait for more workers to join in.

## How to use the models

For all public swarms you can use the Petals SDK in the [usual way](https://github.com/bigscience-workshop/petals). Here is an example:

```python
from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM

# Choose any model available at https://health.petals.dev
model_name = "mistralai/Mixtral-8x22B-Instruct-v0.1"

# Connect to a distributed network hosting model layers
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoDistributedModelForCausalLM.from_pretrained(model_name)

# Run the model as if it were on your computer
inputs = tokenizer("A cat sat", return_tensors="pt")["input_ids"]
outputs = model.generate(inputs, max_new_tokens=5)
print(tokenizer.decode(outputs[0]))  # A cat sat on a mat...
```

This path is great if you are a dev with python installed, and don't mind installing the Petals SDK. If you want an install-free path, Kalavai deploys a single endpoint for models, which allows you to do inference via gRPC and HTTP requests. Here is a request example:

```python
"""
More info: https://github.com/petals-infra/chat.petals.dev

Required: pip install websockets
"""
import time
import json
import websockets
import asyncio


URL = "192.168.68.67:31220" # <-- change for the kalavai endpoint
MODEL_NAME = "mistralai/Mixtral-8x22B-Instruct-v0.1" # <-- change for the models available in Kalavai PETALS pool.


async def ws_generate(text, max_length=100, temperature=0.1):
    async with websockets.connect(f"ws://{URL}/api/v2/generate") as websocket:
        try:
            await websocket.send(
                json.dumps({"model": MODEL_NAME, "type": "open_inference_session", "max_length": max_length})
            )
            response = await websocket.recv()
            result = json.loads(response)

            if result["ok"]:
                await websocket.send(
                    json.dumps({
                        "type": "generate",
                        "model": MODEL_NAME,
                        "inputs": text,
                        "max_length": max_length,
                        "temperature": temperature
                    })
                )
                response = await websocket.recv()
                return json.loads(response)
            else:
                return response
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    t = time.time()
    output = asyncio.get_event_loop().run_until_complete(
        ws_generate(text="Tell me a story: ")
    )
    final_time = time.time() - t
    print(f"[{final_time:.2f} secs]", output)
    print(f"{output['token_count'] / final_time:.2f}", "tokens/s")
```

**NOTE**: the endpoints are only available within worker nodes, not from any other computer.


## Stop sharing

You can either pause sharing, or stop and leave the pool altogether (don't worry, you can rejoin using the same steps above anytime). 

To pause sharing (but remain on the pool), run the following command:

```bash
kalavai pool pause
```

When you are ready to resume sharing, run:
```bash
kalavai pool resume
```

To stop and leave the pool, run the following:

```bash
kalavai pool stop
```


## FAQs

### Can I join (and leave) whenever I want?

Yes, you can, and we won't hold a grudge if you need to use your computer. You can pause or quit altogether as indicated [here](#stop-sharing).

### What is in it for me?

If you decide to share your compute with the community, not only you'll get access to all the models we deploy in it, but you will also gather credits in Kalavai, which will be redeemable for computing in any other public pool (this feature is coming really soon).

### Is my data secured / private?

The public pool in Kalavai has the same level of privacy and security than the general Petals public swarm. See their privacy details [here](https://github.com/bigscience-workshop/petals/wiki/Security,-privacy,-and-AI-safety). In the future we will improve support for private swarms; at the moment private swarms are a beta feature for all kalavai pools that can be used via the [petals template](/templates/petals/README.md).

### Is my GPU constantly being used?

Yes and no. The model weights for the shard you are responsible for are loaded in GPU memory for as long as your machine is sharing. However, this does not mean the GPU is active (doing computing) constantly; computation (and hence the vast majority of energy comsumption) only happens when your shard is summoned to process inference requests.

If at any point you need your GPU memory back, [pause or stop sharing](#stop-sharing) and come back when you are free.
