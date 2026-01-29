# Welcome to Kalavai

Kalavai is an **open source** platform that unlocks **computing from spare capacity**. It aggregates resources from multiple sources to increase your computing budget and run large AI workloads.  

## Core features

Kalavai helps teams use GPU resources more efficiently. It acts as a **control plane for all your GPUs**, wherever they are: local, on prem and multi-cloud. 

- Increase GPU utilisation from your devices (fractional GPU).
- Multi-node, multi-GPU and multi-architecture support (AMD and NVIDIA). 
- **Aggregate** computing resources from **multiple sources**: home desktops, on premise servers<0>, multi cloud VMs, raspberry pi's, etc. Including our [own GPU fleets](https://platform.kalavai.net).
- **Ready-made templates to deploy common AI building blocks**: model inference (vLLM, llama.cpp, SGLang), GPU clusters (Ray, GPUStack), automation workflows (n8n and Flowise), evaluation and monitoring tools (Langfuse), production dev tools (LiteLLM, OpenWebUI) and more.
- [Easy to expand](https://github.com/kalavai-net/kalavai-templates) to custom workloads

## Getting started

The best way to getting started is to check out our [start guide](getting_started.md) for a step-by-step guide on how to get started. This is the recommended entry point for those that wish to explore the basics of Kalavai.


## Core components

Kalavai **turns devices into a scalable LLM platform**. It connects multiple machines together and manages the distribution AI workloads on them.

There are three core components:

- **Kalavai client**: python CLI program that lets users create and interact with GPU pools distributed across multiple machines.
- **Seed node**: master / server machine that initialises and manages a GPU pool. This is the node where the client runs the start command (`kalavai pool start <pool>`). Note that seed nodes must remain on and available for the platform to remain operational.
- **Worker node**: any machine that joins a pool, where the AI workload will be deployed to. This are nodes that run the join command (`kalavai pool join <token>`)

Typically a client will be installed in both the seed and worker nodes, but since v0.5.0, clients can also be installed on external machines. This is useful to be able to connect and send work to your pool from any machine.


### How it works?

To create a GPU pool, you need a **seed node** which acts as a control plane. It handles bookkeeping for the pool. With a seed node, you can generate join tokens, which you can share with other machines --**worker nodes**.

The more worker nodes you have in a pool, the bigger workloads it can run. _Note that the only requirement for a fully functioning pool is a single seed node._

Once you have a pool running, you can deploy workloads using [template jobs](templates.md). These are community integrations that let users deploy AI using multiple frameworks (such as vLLM, SGLang, llama.cpp and n8n). A template makes using Kalavai really easy for end users, with a parameterised interface, and it also makes the **platform infinitely expandable**.

---

## Kalavai platform

For a fully managed computing pool, consider [our managed service](https://platform.kalavai.net).

- Managed seed instance for over-the-internet pools
- Encrypted communication with VPN
- Access to flexible and scalable GPUs fleet from Kalavai

Check out our [documentation](./managed/overview.md) for more details.


## Want to be notified of the latest features? 

Subscribe to our [substack channel](https://kalavainet.substack.com/), where we regularly publish news, articles and updates.

[Join our discord community](https://discord.gg/YN6ThTJKbM){:target="_blank" .md-button .md-button--primary}