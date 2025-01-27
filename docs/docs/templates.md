---
tags:
  - integrations
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

Where <template name> refers to one of the supported templates above, and <template values> is a local yaml file containing the parameters of the job. See [examples](https://github.com/kalavai-net/kube-watcher/tree/main/templates) for more information.


## List of available templates

- [vLLM](https://github.com/kalavai-net/kube-watcher/tree/main/templates): deploy your favourite LLMs in distributed machines.
- [llama.cpp](https://github.com/kalavai-net/kube-watcher/tree/main/templates): deploy llama.cpp models (CPU and GPU) in distributed machines.
- [Aphrodite](https://github.com/kalavai-net/kube-watcher/tree/main/templates): deploy your favourite LLMs in distributed machines.
- [Petals](https://github.com/kalavai-net/kube-watcher/tree/main/templates): bit-torrent style deployment of LLMs
- [litellm](https://github.com/kalavai-net/kube-watcher/tree/main/templates): Unified LLM API.
- [playground](https://github.com/kalavai-net/kube-watcher/tree/main/templates): Unified UI playground.


## How to contribute

Do you want to **develop your own template** and share it with the community? We are working on a path to make it easier for developers to do so. Hang on tight! But for now, head over to [our repository](https://github.com/kalavai-net/kube-watcher/tree/main/templates#how-to-contribute) and check the examples in there.



## Why is *[insert preferred application]* not supported?

If your preferred distributed ML application is not yet supported, [let us know](https://github.com/kalavai-net/kalavai-client/issues)! Or better yet, add it and [contribute to community integrations](https://github.com/kalavai-net/kube-watcher/tree/main/templates).
