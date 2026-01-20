---
tags:
  - integrations
  - jobs
  - LLM engines
  - ray
---
# Develop with Kalavai

> Work in progress

Template jobs built by Kalavai and the community make deploying distributed LLMs easy for end users.

Templates are like recipes, where developers describe what worker nodes should run, and users customise the behaviour via pre-defined parameters. Kalavai handles the heavy lifting: workload distribution, communication between nodes and monitoring the state of the deployment to restart the job if required.

Using the client, you can list what templates your LLM pool supports:

```bash
$ kalavai job templates

[10:51:29] Templates available in the pool
           ['vllm', 'aphrodite', 'llamacpp', 'petals', 'litellm', 'playground', 'boinc', 'gpustack']
```

Deploying a template is easy:
```bash
kalavai job run <template name> --values <template values>
```

Where `<template name>` refers to one of the supported templates above, and `<template values>` is a local yaml file containing the parameters of the job. See [examples](https://github.com/kalavai-net/kalavai-templates) for more information.


## List of available templates

We currently support out of the box the following AI engines:

- [vLLM](https://docs.vllm.ai/en/latest/): most popular GPU-based model inference.
- [Ray Clusters](https://docs.ray.io/en/latest/serve/index.html) inference.
- [GPUstack](https://docs.gpustack.ai/0.4/overview/) (experimental)

Coming soon:

- [llama.cpp](https://github.com/ggerganov/llama.cpp): CPU-based GGUF model inference.
- [SGLang](https://github.com/sgl-project/sglang): Super fast GPU-based model inference.
- [n8n](https://n8n.io/) (experimental): no-code workload automation framework.
- [Flowise](https://flowiseai.com/) (experimental): no-code agentic AI workload framework.
- [Speaches](https://speaches.ai/): audio (speech-to-text and text-to-speech) model inference.
- [Langfuse](https://langfuse.com/) (experimental): open source evaluation and monitoring GenAI framework.
- [OpenWebUI](https://docs.openwebui.com/): ChatGPT-like UI playground to interface with any models.
- [diffusers](https://huggingface.co/docs/diffusers/en/index) (experimental)
- [RayServe](https://docs.ray.io/en/latest/serve/index.html) inference.
- [GPUstack](https://docs.gpustack.ai/0.4/overview/) (experimental)


## How to contribute

Do you want to **develop your own template** and share it with the community? We are working on a path to make it easier for developers to do so. Hang on tight! But for now, head over to [our repository](https://github.com/kalavai-net/kalavai-templates) and check the examples in there.



## Why is *[insert preferred application]* not supported?

If your preferred distributed ML application is not yet supported, [let us know](https://github.com/kalavai-net/kalavai-client/issues)! Or better yet, add it and [contribute to community integrations](https://github.com/kalavai-net/kalavai-templates).
