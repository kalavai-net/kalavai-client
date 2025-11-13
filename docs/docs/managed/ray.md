---
tags:
  - ray
  - distributed ML
---

> Beta access only. Register your interest [here](https://kalavai.net/beta)

# Ray in Kalavai

Create, manage and deploy Ray workloads in Kalavai.


Autoscaling to zero
Flexible on demand scaling of GPUs
Explain params + example
What the endpoints mean

## What is Ray?

[Ray](https://docs.ray.io/en/latest/index.html) is a distributed framework for scaling Python and ML workloads. Kalavai’s managed Ray clusters let you launch distributed training or inference tasks without setting up or managing nodes.

**Platform features**:

- Create Ray clusters that autoscale to your needs without dealing with infrastructure
- Highly configurable (python version, CUDA kernels, node capabilities)
- Flexible and affordable access to thousands of data centre-level GPUs


## Getting Started


Install the Kalavai CLI

pip install kalavai


Authenticate with your Kalavai account

kalavai login


Create a Ray Cluster

kalavai cluster create --framework ray --name my-ray-cluster --gpus 4


Connect to your cluster

kalavai cluster connect my-ray-cluster


Submit your Ray job

ray submit my-ray-cluster train.py

Cluster Management

List active clusters: kalavai cluster list

Scale up/down GPUs: kalavai cluster scale my-ray-cluster --gpus 8

Delete cluster: kalavai cluster delete my-ray-cluster