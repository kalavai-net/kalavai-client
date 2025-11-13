---
tags:
  - GPUstack
  - GPU cluster
  - LLM deployment
---

> Beta access only. Register your interest [here](https://kalavai.net/beta)

# GPUStack in Kalavai

Create, manage and deploy LLMs across multiple devices with GPUStack in Kalavai.


Manage your cluster of GPUs
Easy GUI deployment of models
Heterogeneous GPUs (NVIDIA, AMD)
Explain params + example



## What is GPUStack?

[GPUStack](https://docs.gpustack.ai/latest/overview/) is an open-source system for managing GPU scheduling and sharing across workloads. Kalavai offers managed GPUStack clusters that automatically allocate resources to the GPUStack pool.

**Platform features**:

- Create GPUStack clusters with mix hardware (NVIDIA, AMD) without dealing with infrastructure
- Highly configurable (number of GPUs, node capabilities)
- Flexible and affordable access to thousands of data centre-level GPUs


## Quick Start

Create a GPUStack Cluster

kalavai cluster create --framework gpustack --name my-stack --gpus 8


Submit a Job

kalavai job submit --cluster my-stack --script train.sh


Monitor Progress

kalavai job logs --cluster my-stack --job <job_id>


Scale Resources Dynamically

kalavai cluster scale my-stack --gpus 12

Benefits

Auto-scaling GPU pools

Cost-efficient scheduling across workloads

Unified monitoring dashboard via Kalavai Console