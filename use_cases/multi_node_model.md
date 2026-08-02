---
tags:
  - deployment
  - llm inference
  - llamacpp
  - vllm
  - multi node
  - multi gpu
---


# Distributed model deployment

| WIP: coming soon

Deploying across multiple devices, you can use any of the [available templates for model deployment](single_node_model.md), and configure it to use more than one worker. This could be to use GPUs on multiple devices, or to increase the memory pool available by distributing the weight load across.


## Using the model

Templates deploy an OpenAI-compatible API service that can be used to interact with the deployed models. See our [inference section](../inference/overview.md) for example code snippets on various model modalities.