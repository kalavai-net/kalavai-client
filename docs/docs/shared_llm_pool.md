---
tags:
  - crowdsource
  - shared llm
---

# Shared pools for LLM deployment

> Beta feature: we are trialing shared pools. If you encounter any issues, please [submit a ticket in our GitHub repo](https://github.com/kalavai-net/kalavai-client/issues).

Shared pools in `Kalavai` are an easy way to expand your computing power beyond a single machine, with zero-devops knowledge. Ever wanted to deploy the biggest 405B Llama 3.3 model but have to compromise (and quantize!) because your GPU will only fit the 8B version? Kalavai **aggregates the GPUs, CPUs and RAM memory** from any compatible machine and makes it ready for LLM workflows. All you need is three steps to get your supercomputing cluster going!

1) Start a pool with the kalavai client
2) Use the joining token to connect other machines to the pool
3) Deploy LLMs with ready-made templates!

In this guide, we'll show **how to create your very own private shared pool**, ideal for teams of developers that want to supercharge their AI without opening it to the public.


### (TL;DR) Skip configuring the pool and access public resources

We thought the community may be interested in a public version, so we have created a public shared pool that anyone can join. It is truly public (anyone can join) and shared (resources are pooled together, and anyone can see and use each other's LLMs).

We are committed to advancing community computing, and that's why not only we are showing how anyone can create their own pool with their devices, but access to the public instance is free.


## How to set it up

> Coming soon!

If you are using our public shared pool, you can skip this step. This is only for those that want to create a private pool on their own network.

Configure pool: minio size and replicas, secrets and passwords

Install kalavai client on seed node

Connect other machines

Create storage for LiteLLM

Configure LiteLLM: storage class name, password, master key

Deploy LiteLLM template

Generate a virtual key


## How to use it

### Check current models

kalavai job list

curl /v1/models for ready models


### Use models

curl

python



### Deploy new models

Use the virtual key for the pool to deploy models via the vLLM template:

- Configure template (model_id, pipeline parallel size, litellm key, workers)
- Deploy template

