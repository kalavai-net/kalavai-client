---
tags:
  - GPUstack
  - GPU cluster
  - LLM deployment
---

> Beta access only. Register your interest [here](https://kalavai.net/beta)

# GPUStack in Kalavai

Create, manage and deploy LLMs across multiple devices with GPUStack in Kalavai.


## What is GPUStack?

[GPUStack](https://docs.gpustack.ai/latest/overview/) is an open-source system for managing GPU scheduling and sharing across workloads. Kalavai offers managed GPUStack clusters that automatically allocate resources to the GPUStack pool.

**Platform features**:

- Create GPUStack clusters with mix hardware (NVIDIA, AMD) without dealing with infrastructure
- Highly configurable (number of GPUs, node capabilities)
- Flexible and affordable access to thousands of data centre-level GPUs


## Getting Started

[Log in](https://platform.kalavai.net) to your Kalavai account and navigate to the ```Clusters``` page. This section allows you to create, manage and connect to your GPU clusters. 

![Clusters page](./assets/blank_clusters.png)

As long as you are within your resource quota (as indicated under ```Available Resources```) you can create as many clusters as you need --even multiple of the same type. You can create a cluster by selecting any of the supported templates (growing!) under the ```Create new Cluster``` section.

## Create a GPUStack cluster

Select ```GPUStack Cluster``` on the list of cluster templates to configure your GPUStack cluster.

![Create gpustack cluster](./assets/create_gpustack.png)

### Configuring your GPUStack cluster

The GPUStack template allows you to configure your cluster instance to your needs. 

![GPUStack template config options](./assets/gpustack_config_options.png)

Here's a list of key parameters:

- `admin_password` (default: `"password"`, required): Default password for the `admin` user (required to login to the UI)
- `working_memory` (default: `5`, optional): Temporary storage (in GB) to cache model weights.
- `cuda_workers` (default: `1`, required): Number of remote NVIDIA workers (for tensor and pipeline parallelism).
- `rocm_workers` (default: `1`, required): Number of remote AMD ROCm workers (for tensor and pipeline parallelism).
- `token` (default: `"sometoken"`, required): Token used to load the cluster or authenticate access.
- `hf_token` (default: `null`, required): Huggingface token, required to load model weights.
- `cpus` (default: `2`, optional): CPUs per single worker (final count = cpus * num_workers).
- `gpus` (default: `1`, optional): GPUs per single worker (final count = gpus * num_workers).
- `memory` (default: `12`, optional): RAM memory per single worker (final count = memory * num_workers)
  
  
When you are ready, click on `Deploy Cluster`. The GPUStack instance may take a few minutes to spin up. Check the status of the pool under `Your clusters`. Note that the cluster will be ready for access as soon as the head node is ready. Workers may be queued up to join based on the number and types requested.


#### Example: Hybrid GPU cluster

GPUStack lets you connect heterogeneous GPU devices to a single instance. For instance, you may connect 4 NVIDIA GPUs and 8 AMD GPUs with the following settings:

- `cuda_workers`: 4
- `rocm_workers`: 8

When you deploy models in the GPUStack interface you can target either of the GPUs or do distributed deployments across multiple devices.



### Connecting to your cluster

Once the status of the cluster is `Ready` you are ready to put the instance to work. Each GPUStack cluster exposes a single endpoint for you to connect to the UI interface. 

Click on the UI endpoint of your GPUStack cluster. You will be presented with the login screen. Use the following default credentials:

- Username: `admin`
- Password: `<password set during cluster config>`


![GPUStack login](./assets/gpustack_login.png)

You can monitor the status of the workers and GPUs under the Resources section of your GPUStack cluster.

![GPU worker gpus](./assets/gpu_workers.png)

### Deploy a model

Follow the official examples from GPUStack to [deploy models](https://docs.gpustack.ai/latest/using-models/using-large-language-models/) and more.

## What next

GPUStack [documentation](https://docs.gpustack.ai/latest/overview/)