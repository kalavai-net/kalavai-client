---
tags:
  - kalavai-client
  - cli
  - install
  - requirements
---

# Getting started

The `kalavai` client is the main tool to interact with the Kalavai platform, to create and manage both local and public pools and also to interact with them (e.g. deploy models). Let's go over its installation. 

From release **v0.5.0, you can now install `kalavai` client in non-worker computers**. You can run a pool on a set of machines and have the client on a remote computer from which you access the LLM pool. Because the client only requires having python installed, this means more computers are now supported to run it.


### Requirements

- A laptop, desktop or Virtual Machine
- Docker engine installed (for [linux](https://docs.docker.com/engine/install/), [Windows and MacOS](https://docs.docker.com/desktop/)) with [privilege access](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities).


### Requirements to run the client

- Python 3.6+
- For seed and workers: Docker engine installed (for [linux](https://docs.docker.com/engine/install/), [Windows and MacOS](https://docs.docker.com/desktop/)) with [privilege access](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities).


### Install the client

The client is a python package and can be installed with one command:

```bash
pip install kalavai-client
```

## Public LLM pools: crowdsource community resources

This is the **easiest and most powerful** way to experience Kalavai. It affords users the full resource capabilities of the community and access to all its deployed LLMs, via an [OpenAI-compatible endpoint](https://kalavai-net.github.io/kalavai-client/public_llm_pool/#single-api-endpoint) as well as a [UI-based playground](https://kalavai-net.github.io/kalavai-client/public_llm_pool/#ui-playground).

Check out [our guide](https://kalavai-net.github.io/kalavai-client/public_llm_pool/) on how to join and start deploying LLMs.


## Createa a local, private LLM pool

Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you wish to join computers in different locations / networks, check [managed kalavai](#public-pools-crowdsource-community-resources).

### 1. Start a seed node

Simply use the client to start your seed node:

```bash
kalavai pool start <pool-name>
```

Now you are ready to add worker nodes to this seed. To do so, generate a joining token:
```bash
$ kalavai pool token --user

Join token: <token>
```

### 2. Add worker nodes

Increase the power of your AI pool by inviting others to join.

Copy the joining token. On the worker node, run:

```bash
kalavai pool join <token>
```

### 3. Attach more clients

You can now connect to an existing pool from any computer -not just from worker nodes. To connect to a pool, run:

```bash
kalavai pool attach <token>
```

This won't add the machine as a worker, but you will be able to operate in the pool as if you were. This is ideal for remote access to the pool, and to use the pool from machines that cannot run workers (docker container limitations).


### Hardware compatibility:
- `amd64` or `x86_64` CPU architecture
- (optional) NVIDIA GPU
- AMD and Intel GPUs are currently not supported (yet!)


## What's next

Now that you know how to get a pool up and running, check our [end to end tutorial](./self_hosted_llm_pool.md) on how to sllf host an LLM Pool, or go full on easy-mode by [joining a public pool](public_llm_pool.md).
