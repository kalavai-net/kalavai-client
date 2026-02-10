---
tags:
  - managed platform
  - hosted clusters
---

# Kalavai Developer Documentation

Welcome to the Kalavai Developer Docs — your guide to building, training, and deploying AI workloads on Kalavai’s distributed compute platform.

Kalavai leverages spare data center capacity to deliver flexible, cost-effective compute for machine learning, AI inference, and large model hosting.


## What is the Kalavai Platform

Kalavai Platform is a managed computing platform that simplifies access to GPU compute and LLM hosting. It builds on our [open-source orchestration library](https://github.com/kalavai-net/kalavai-client), integrating directly with tools you already use — like `Ray` and `GPUStack` — to provide on-demand distributed compute for AI workloads.


### Efficient cost and low infrastructure overhead

Our platform abstracts the complexity of provisioning and managing GPU clusters, while optimizing performance and cost through dynamic utilization of spare capacity. When using the Kalavai Platform, users have direct access to a large fleet of data centre level GPUs at the lowest price in the market.

| Product                       | Description                                                                                                 |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Managed GPU Clusters**      | Spin up distributed `Ray` and `GPUStack` clusters for training, hyperparameter tuning, reinforcement learning and custom workloads.           |
| **Async Inference & LLM queue**   | Affordable LLM inference for large scale intelligence projects |
| **Model fine tuning** | Easily customise LLM to your data |


## Beta Tester Program 🚀

We’re currently in Beta, and inviting developers and research teams to get early access to Kalavai. We're seeking developers who have hands-on experience with one or more of the following frameworks to participate in our beta testing program: `Ray`, `Unsloth`, `Axolotl` or `GPUStack`.

👉 [Join the Beta Tester Program](https://kalavai.net/beta) to get started.

Join our exclusive [Discord community](https://discord.gg/YN6ThTJKbM) for beta testers.

## Get started for free

Get a free account [here](https://platform.kalavai.net) to access the Kalavai Platform. All accounts come with access to free resources, like CPUs, GPUs and memory.

During the Beta Testing phase, you will be asked to join the Beta Program the first time you login. This will grant you free resources to test the platform.

![Join beta testing](./assets/images/join_beta.png)


## Available Resources

All accounts get a default resources quota, which includes the core resources you are allowed to utilise in your `Serverless` deployments. These are the default resources for a free account:

- `8 CPUs`
- `32 GB RAM`
- `2 NVIDIA GPUs`
- `0 AMD GPUs`

Note that this is not resources that have been allocated to your account. It simply states the maximum resources your deployments can utilise at once. The `Serverless` page shows the utilised resources and the quota under `Available Resources`.

![Resource quotas](./assets/images/resource_quota.png)

To increase your assigned quota during the beta testing period, use the `Request Quota Increase` button under `Available Resources`.


## What next?

Head over to the [GPU fleet guide](./gpu_fleet.md) to create your first pool and get going with AI deployments!
