---
tags:
  - concepts
  - architecture
  - pool
---


# Core components

Kalavai **turns devices into a scalable LLM platform**. It connects multiple machines together and manages the distribution LLM workloads on them.

There are three core components:

- **Kalavai client**: python CLI program that lets users create and interact with LLM pools distributed across multiple machines.
- **Seed node**: master / server machine that initialises and manages an LLM pool. This is the node where the client runs the start command (`kalavai pool start <pool>`). Note that seed nodes must remain on and available for the platform to remain operational.
- **Worker node**: any machine that joins an LLM pool, where the LLM workload will be deployed to. This are nodes that run the join command (`kalavai pool join <token>`)

Typically a client will be installed in both the seed and worker nodes, but since v0.5.0, clients can also be installed on external machines. This is useful to be able to connect and send work to your pool from any machine.


## How it works?

To create an LLM pool, you need a **seed node** which acts as a control plane. It handles bookkeeping for the pool. With a seed node, you can generate join tokens, which you can share with other machines --**worker nodes**.

The more worker nodes you have in a pool, the bigger workloads it can run. _Note that the only requirement for a fully functioning pool is a single seed node._

Once you have a pool running, you can easily deploy workloads using [template jobs](templates.md). These are community integrations that let users deploy LLMs using multiple model engines. A template makes using Kalavai really easy for end users, with a parameterised interface, and it also makes the **platform infinitely expandable**.