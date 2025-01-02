# Petals

[Petals](https://github.com/bigscience-workshop/petals) is a python library that lets users run LLMs at home, BitTorrent-style. It supports distributed deployment and fine-tuning of the following models: Llama 3.1 (up to 405B), Mixtral (8x22B), Falcon (40B+) or BLOOM (176B).

In Kalavai you can deploy both public nodes (workers) and [private swarms](https://github.com/bigscience-workshop/petals/wiki/Launch-your-own-swarm).

## Public workers

To deploy workers to the public Petals server, you can set the initial peers to empty, and define the model you want in your values.yaml. In this example, we'll deploy Llama3.1 8B Instruct model:

```yaml
- name: model_id
  value: "meta-llama/Llama-3.1-8B-Instruct"
  default: "meta-llama/Llama-3.1-8B-Instruct"
  description: ""
```

The model shards for each worker will be deployed on each node's local drive, under `/kalavai`. You can define how many nodes you'd like to work for the model via the `max_workers` parameter.

```yaml
- name: max_workers
  value: "3"
  default: "1"
  description: "Maximum number of workers to spawn in the cluster"
```

Note that workers will start contributing to the model deployment even if you don't reach the maximum workers requrested. The magic of Petals!

For more parameters, check the [example yaml](/templates/petals/examples/public_workers.yaml) provided. 

Once you are ready to start deployment, use the following command pointing the `values` to our [example yaml](/templates/petals/examples/public_workers.yaml)

```bash
kalavai job run petals --values examples/public_workers.yaml
```

You can monitor the progress of the deployment as usual:

```bash
$ kalavai job list
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Deployment ┃ Status                         ┃ Workers    ┃ Endpoint                                    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ llama3-8b  │ [2024-12-22T11:54:05Z] Pending │ Pending: 4 │ http://192.168.68.67:31820 (mapped to 5000) │
│            │                                │            │ http://192.168.68.67:30224 (mapped to 5001) │
└────────────┴────────────────────────────────┴────────────┴─────────────────────────────────────────────┘
```

This will expose the addresses for the two available endpoints:
- (mapped to 5000): Health monitoring for all models.
- (mapped to 5001): Chat UI and API endpoint to query the model

To check the health UI, point your browser to `http://192.168.68.67:31820`. You should start seeing the model shards appearing.

![Petals](/templates/petals/examples/petals.png.png)

Once the shards are all in green you should be able to [use the model for inference](#use-the-models).


## Private swarm

**Coming soon!**


## Use the models

The common way to interact with your model is through the Petals python API, which requires installing the package:

```python
from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM

model_name = "meta-llama/Llama-3.1-8B-Instruct"

# Connect to a distributed network hosting model layers
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoDistributedModelForCausalLM.from_pretrained(model_name)

# Run the model as if it were on your computer
inputs = tokenizer("What is the capital of France?", return_tensors="pt")["input_ids"]
outputs = model.generate(inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0]))  # A cat sat on a mat...
```

Run the following:

```bash
pip install git+https://github.com/bigscience-workshop/petals
python examples/local_inference.py
```

Alternatively, Kalavai deploys a helper API endpoint along with the workers that you can use, without the need to further download model shards or installing the petal package. We have an [example](examples/remote_endpoint.py) of how to do this; just replace the endpoint with the 5001 endpoint above:

```bash
URL = "192.168.68.67:30224"
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
```

## Delete deployment

Remove the job with the usual:

```bash
kalavai job delete llama3-8b
```