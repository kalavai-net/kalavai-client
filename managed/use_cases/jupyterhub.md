---
tags:
  - distributed
  - multi GPU
  - jupyterlab
  - jupyterhub
  - notebooks
---

| WIP |
|-----|
| This page is currently under development |

Managed experience for JupyterHub with multi-GPU support. The best way to have interactive sessions with multi-GPU, distributed environments.

## What is JupyterHub?

[JupyterHub](https://jupyter.org/hub) is a multi-user server for Jupyter notebooks. It allows multiple users to access Jupyter notebooks in a shared environment. It's great for AI development and an easy way to interact with GPU-based machines without the complexity of SSH connections.

### Why JupyterHub in Kalavai

Kalavai offers a managed way to deploy JupyterHub instances in your resources (if using our open source platform) or in our cloud. The biggest advantage is that with Kalavai, JupyterHub comes with multi-GPU support out of the box. You can easily access multiple GPUs from within your Jupyter notebooks or terminal via access so your own autoscalable Ray cluster.

Features:

- Multi-GPU support
- Auto-scaling so you only engage GPUs when needed
- Customisable and version controlled: set your own base images and let developers loose with their experiments; broken dependencies? Just redeploy and start over


## Deploy a JupyterHub

In your Kalavai Pool, go to `Jobs` and create a new job. Select `JupyterHub` as the template and configure the GPU resources you need.

In the template parameters section of the deployment, you can configure the resources for the JupyterHub instance, under `Advanced parameters`.

![JupyterHub configuration](/docs/docs/managed/assets/images/jupyterhub_config.png)



### Single vs multi-GPU

Two options:
- Single instance JupyterHub with a local GPU
- Multi-GPU JupyterHub with direct access to multi-GPU environment via Ray cluster.


## Single GPU JupyterHub (default)

Best for quick prototyping, development of local features that require a GPU.




## Multi-GPU JupyterHub

Best for heavy workloads, distributed training, and large-scale machine learning projects, where direct access to multiple GPUs is required.

Single JupyterHub instance with direct access to a Ray cluster for easy workload distribution.


![Multi-GPU JupyterHub configuration](/docs/docs/managed/assets/images/jupyterhub_multi_gpu.png)
