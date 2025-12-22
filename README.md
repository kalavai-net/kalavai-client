![Kalavai logo](docs/docs/assets/icons/logo_no_background.png)

<div align="center">

![GitHub Release](https://img.shields.io/github/v/release/kalavai-net/kalavai-client) ![PyPI - Downloads](https://img.shields.io/pypi/dm/kalavai-client?style=social)
 ![GitHub contributors](https://img.shields.io/github/contributors/kalavai-net/kalavai-client) ![GitHub License](https://img.shields.io/github/license/kalavai-net/kalavai-client) ![GitHub Repo stars](https://img.shields.io/github/stars/kalavai-net/kalavai-client) [![Dynamic JSON Badge](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fdiscord.com%2Fapi%2Finvites%2FYN6ThTJKbM%3Fwith_counts%3Dtrue&query=%24.approximate_member_count&logo=discord&logoColor=white&label=Discord%20users&color=green)](https://discordapp.com/channels/1295009828623880313) [![Signup](https://img.shields.io/badge/Kalavai-Signup-brightgreen)](https://platform.kalavai.net) 

</div>

### ⭐⭐⭐ **Kalavai platform is open source, and free to use in both commercial and non-commercial purposes. If you find it useful, consider supporting us by [giving a star to our GitHub project](https://github.com/kalavai-net/kalavai-client), joining our [discord channel](https://discord.gg/YN6ThTJKbM) and follow our [Substack](https://kalavainet.substack.com/).**



# Kalavai aggregates compute from spare GPU capacity

> Kalavai is an **open source** platform that unlocks **computing** from spare capacity. It aggregates resources from multiple sources to increase your computing budget and run large AI workloads.  

## Core features

Kalavai's goal is to make using AI workloads in real applications accessible and affordable to all.

- Increase GPU utilisation from your devices (fractional GPU).
- Multi-node, multi-GPU and multi-architecture support (AMD and NVIDIA). 
- **Aggregate** computing resources from **multiple sources**: home desktops, work computers, multi cloud VMs, raspberry pi's, Mac, etc.
- **Ready-made templates to deploy common AI building blocks**: model inference (vLLM, llama.cpp, SGLang), GPU clusters (Ray, GPUStack), automation workflows (n8n and Flowise), evaluation and monitoring tools (Langfuse), production dev tools (LiteLLM, OpenWebUI) and more.
- [Easy to expand](https://github.com/kalavai-net/kube-watcher/tree/main/templates) to custom workloads


<details>

**<summary>Powered by Kalavai</summary>**

- [CoGen AI](https://cogenai.kalavai.net): A community hosted alternative to OpenAI API for unlimited inference.
- [Create your own Free Cursor/Windsurf Clone](https://www.youtube.com/watch?v=6zHSo7oeCDQ&t=21s)


</details>


### Latest updates

- November: Kalavai is now opening a managed service to create and manage AI workloads on a fleet of GPUs. We are inviting Beta Testers for early access. If you are interested [Apply here](https://kalavai.net/beta)
- September: Kalavai now supports Ray clusters for massively distributed ML.
- August 2025: Added support for AMD GPUs (experimental)
- July 2025: Added support for GPUStack clusters for managed LLM deployments (experimental).
- June 2025: Native support for Mac and Raspberry pi devices (ARM).
- May 2025: Added support for diffusion pipelines (experimental)
- April 2025: Added support for workflow automation engines n8n and Flowise (experimental)
- March 2025: Added support for AI Gateway LiteLLM

<details>
<summary>More news</summary>

- 20 February 2025: New shiny GUI interface to control LLM pools and deploy models- 31 January 2025: `kalavai-client` is now a [PyPI package](https://pypi.org/project/kalavai-client/), easier to install than ever!
- 27 January 2025: Support for accessing pools from remote computers
- 9 January 2025: Added support for [SGLang](https://github.com/aphrodite-engine/aphrodite-engine) models
- 9 January 2025: Added support for [vLLM](https://github.com/aphrodite-engine/aphrodite-engine) models
- 9 January 2025: Added support for [llama.cpp](https://github.com/aphrodite-engine/aphrodite-engine) models
- 24 December 2024: Release of [public BOINC pool](/docs/docs/boinc.md) to donate computing to scientific projects
- 23 December 2024: Release of [public petals swarm](/docs/docs/petals.md)
- 24 November 2024: Common pools with private user spaces

</details>

### Support for AI engines

We currently support out of the box the following AI engines:

- [vLLM](https://docs.vllm.ai/en/latest/): most popular GPU-based model inference.
- [llama.cpp](https://github.com/ggerganov/llama.cpp): CPU-based GGUF model inference.
- [SGLang](https://github.com/sgl-project/sglang): Super fast GPU-based model inference.
- [n8n](https://n8n.io/) (experimental): no-code workload automation framework.
- [Flowise](https://flowiseai.com/) (experimental): no-code agentic AI workload framework.
- [Speaches](https://speaches.ai/): audio (speech-to-text and text-to-speech) model inference.
- [Langfuse](https://langfuse.com/) (experimental): open source evaluation and monitoring GenAI framework.
- [OpenWebUI](https://docs.openwebui.com/): ChatGPT-like UI playground to interface with any models.
- [diffusers](https://huggingface.co/docs/diffusers/en/index) (experimental)
- [RayServe](https://docs.ray.io/en/latest/serve/index.html) inference.
- [GPUstack](https://docs.gpustack.ai/0.4/overview/) (experimental)


Not what you were looking for? [Tell us](https://github.com/kalavai-net/kalavai-client/issues) what engines you'd like to see.


> Kalavai is at an **early stage** of its development. We encourage people to use it and give us feedback! Although we are trying to minimise breaking changes, these may occur until we have a stable version (v1.0).


## Want to know more?

- Get a free [Kalavai account](https://platform.kalavai.net) and access unlimited AI.
- Full [documentation](https://kalavai-net.github.io/kalavai-client/) for the project.
- [Join our Substack](https://kalavainet.substack.com/) for updates and be part of our community
- [Join our discord community](https://discord.gg/YN6ThTJKbM)


## Getting started

The `kalavai-client` is the main tool to interact with the Kalavai platform, to create and manage both local and public pools and also to interact with them (e.g. deploy models).


<details>

<summary>Requirements</summary>

For seed nodes:
- A 64 bits x86 based Linux machine (laptop, desktop or VM)
- [Docker engine installed](https://docs.docker.com/engine/install/ubuntu/) with [privilege access](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities).

For workers sharing resources with the pool:

- A laptop, desktop or Virtual Machine. Full support: Linux and Windows; x86 architecture. Limited support: Mac and ARM architecture.
- If self-hosting, workers should be on the same network as the seed node. Looking for over-the-internet connectivity? Check out our [managed seeds](https://platform.kalavai.net)
- Docker engine installed (for [linux](https://docs.docker.com/engine/install/ubuntu/), [Windows and MacOS](https://docs.docker.com/desktop/)) with [privilege access](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities).

### Compatibility matrix

If your system is not currently supported, [open an issue](https://github.com/kalavai-net/kalavai-client/issues) and request it. We are expanding this list constantly.


</details>


### Install the client

The client is a python package and can be installed with one command:

```bash
pip install kalavai-client
```


## Create a a local, private AI pool

You can create and manage your pools with the [kalavai GUI](./docs/docs/gui.md) or the [Command Line Interface (CLI)](./docs/docs/cli.md). For a quick start, get a pool going with:

```bash
kalavai pool start
```

And then start the GUI:

```bash
kalavai gui start
```

This will expose the GUI and the backend services in localhost. By default, the GUI is accessible via [http://localhost:49153](http://localhost:49153).

![Kalavai logo](docs/docs/assets/images/ui_dashboard_multiple.png)

Check out our [getting started guide](https://kalavai-net.github.io/kalavai-client/getting_started/) for next steps on how to add more workers to your pool, or use our [managed seeds service](./docs/docs/managed/overview.md) for over-the-internet AI pools.


## Enough already, let's run stuff!

Check out our use cases documentation for inspiration on what you can do with Kalavai:

- [Multi-GPU LLM](./docs/docs/use_cases/multi_gpu_inference.md)
- [Fine tune](./docs/docs/use_cases/fine_tuning.md)
- [Autoscaling deployments](./docs/docs/use_cases/)
- [BYO Model Gateway](./docs/docs/use_cases/self_hosted_llm_pool.md)
- [Easy LLMs with GPUstack](./docs/docs/use_cases/gpustack.md)
- [Production GPU fleets](./docs/docs/use_cases/ray.md)

## Contribute

Anything missing here? Give us a shout in the [discussion board](https://github.com/kalavai-net/kalavai-client/discussions). We welcome discussions, feature requests, issues and PRs!

- [Join the community](https://github.com/kalavai-net/kalavai-client/) and share ideas!
- Report [bugs, issues and new features](https://github.com/kalavai-net/kalavai-client/issues).
- Help improve our [compatibility matrix](#compatibility-matrix) by testing on different operative systems.
- [Follow our Substack channel](https://kalavainet.substack.com/) for news, guides and more.
- [Community integrations](https://github.com/kalavai-net/kube-watcher/tree/main/templates) are template jobs built by Kalavai and the community that makes deploying distributed workflows easy for users. Anyone can extend them and contribute to the repo.

### Star History

[![Star History Chart](https://api.star-history.com/svg?repos=kalavai-net/kalavai-client&type=Date)](https://star-history.com/#kalavai-net/kalavai-client&Date)


## Build from source

<details>

### Add Secrets to GitHub

You must store your Docker Hub username and the token you just created as secrets in your GitHub repository:

1. Go to your GitHub repository.

2. Navigate to Settings > Security > Secrets and variables > Actions.

3. Click New repository secret.

4. Create the following two secrets:
```
Name: DOCKER_HUB_USERNAME
Value: Your Docker Hub username or organization name.

Name: DOCKER_HUB_TOKEN
Value: The Personal Access Token you copied from Docker Hub.
```

<summary>Expand</summary>

Python version >= 3.10.

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-dev python3-virtualenv python3-venv
virtualenv -p python3.10 env
source env/bin/activate
sudo apt install  python3.10-venv python3.10-dev -y
pip install -U setuptools
pip install -e .[dev]
```

Build python wheels:
```bash
bash publish.sh build
```

</details>

### Unit tests

To run the unit tests, use:

```bash
python -m unittest
```
