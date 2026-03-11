---
tags:
  - managed platform
  - gpu fleet
---


You can create your own GPU fleet cluster to manage multi-GPU deployments. Ideal for:

- Scalable AI inference to cope with dynamic request loads
- Affordable resources with scale to zero by default
- Deploy a Ray cluster for fine tuning or custom distributed workloads


## What's a Kalavai GPU fleet?

A Kalavai fleet, or a GPU pool, is a managed control plane for multi-GPU deployments. Think of it as your own personal AI cloud provider interface, but with none of the devops overhead.

With a GPU fleet you get access to all built-in [kalavai-templates](/docs/docs/templates.md), which let you deploy across GPUs:

- AI models via model engines (vLLM, llama.cpp)
- Ray clusters for training and fine tuning at scale
- Serverless containers



## Requirements

- An account in our [platform](https://platform.kalavai.net)
- [Join the Beta Tester Program](https://kalavai.net/beta)


## Getting started

To create a new Kalavai fleet, head over to the [platform](https://platform.kalavai.net) and navigate to the Serverless page. Click on Create new deployment and select the Kalavai-pool template.

![Create kalavai pool](./assets/images/kalavai_pool.png)
