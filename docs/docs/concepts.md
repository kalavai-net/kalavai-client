---
tags:
  - concepts
  - architecture
---

> Work in progress

# Core concepts

**Under construction**. Come back soon!

A platform to turn everyday devices into a powerful AI cloud

## How it works?

To create an AI cluster, you need a **seed node** which acts as a control plane. It handles bookkeeping for the cluster. With a seed node, you can generate join tokens, which you can share with other machines --**worker nodes**.

The more worker nodes you have in a cluster, the bigger workloads it can run. _Note that the only requirement for a fully functioning cluster is a single seed node._

Once you have a cluster running, you can easily deploy workloads using [template jobs](https://github.com/kalavai-net/kalavai-client/blob/main/templates/README.md). These are community integrations that let users deploy jobs, such as LLM deployments or LLM fine tuning. A template makes using Kalavai really easy for end users, with a parameterised interface, and it also makes the **platform infinitely expandable**.