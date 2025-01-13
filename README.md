![alt text](docs/docs/assets/icons/logo_no_background.png)

<div align="center">

![GitHub Release](https://img.shields.io/github/v/release/kalavai-net/kalavai-client) ![GitHub download count](https://img.shields.io/github/downloads/kalavai-net/kalavai-client/total
) ![GitHub contributors](https://img.shields.io/github/contributors/kalavai-net/kalavai-client) ![GitHub License](https://img.shields.io/github/license/kalavai-net/kalavai-client) ![GitHub Repo stars](https://img.shields.io/github/stars/kalavai-net/kalavai-client) [![Discord](https://img.shields.io/discord/1295009828623880313?logo=discord&label=discord)](https://discordapp.com/channels/1295009828623880313) [![Signup](https://img.shields.io/badge/Kalavai-Signup-brightgreen)](https://platform.kalavai.net)

`⭐ Kalavai is open-source - Support us by leaving a star ⭐`

</div>


# Kalavai: the first platform to crowdsource end to end LLM deployment at scale

### Taming the adoption of Large Language Models

> Kalavai is an **open source** tool that turns **everyday devices** into your very own LLM platform. It aggregates resources from multiple machines, including desktops and laptops, and is **compatible with most model engines** to make LLM deployment and orchestration simple. When you need to **go beyond**, Kalavai public pools **facilitate matchmaking** of resources so anyone in our community can tap into a larger pool of devices. [Potluck](https://en.wikipedia.org/wiki/Potluck#:~:text=A%20potluck%20is%20a%20communal,a%20potluck%20in%20Alberta%2C%20Canada) computing.

<div align="center">

<a href="https://www.producthunt.com/products/kalavai/reviews?utm_source=badge-product_review&utm_medium=badge&utm_souce=badge-kalavai" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/product_review.svg?product_id=720725&theme=neutral" alt="Kalavai - The&#0032;first&#0032;platform&#0032;to&#0032;crowdsource&#0032;AI&#0032;computation | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

</div>

### News updates

- 9 January 2025: Added support for [Aphrodite Engine](https://github.com/aphrodite-engine/aphrodite-engine) models
- 8 January 2025: Release of [a free, public, shared pool](/docs/docs/public_llm_pool.md) for community LLM deployment
- 24 December 2024: Release of [public BOINC pool](/docs/docs/boinc.md) to donate computing to scientific projects
- 23 December 2024: Release of [public petals swarm](/docs/docs/petals.md)
- 24 November 2024: Common pools with private user spaces
- 30 October 2024: Release of our [public pool platform](https://platform.kalavai.net)


## What can Kalavai do?

Kalavai's goal is to make using LLMs in real applications accessible and affordable to all. It's a _magic box_ that **integrates all the components required to make LLM useful in the age of massive computing**, from sourcing computing power, managing distributed infrastructure and storage, using industry-standard model engines and orchestration of LLMs. 

### Aggregate multiple devices in an LLM pool

https://github.com/user-attachments/assets/008f8627-f866-4258-8698-0fd53d5029c5

### Deploy LLMs across the pool

https://github.com/user-attachments/assets/92185e7f-5ea0-4c2e-9002-20deb789ee06

### Single point of entry for all models (GUI + API)

https://github.com/user-attachments/assets/97e894f4-3c6f-4989-8a72-d8543fb058ea

### Support for LLM engines

We currently support out of the box the following LLM engines:

- [vLLM](templates/vllm/README.md)
- [llama.cpp](templates/llamacpp/README.md)
- [Aphrodite Engine](https://github.com/aphrodite-engine/aphrodite-engine)
- [Petals](templates/petals/README.md)

Coming soon:

- [exo](https://github.com/exo-explore/exo)
- [GPUstack](https://docs.gpustack.ai/0.4/overview/)
- [RayServe](https://docs.ray.io/en/latest/serve/index.html)

Not what you were looking for? [Tell us](https://github.com/kalavai-net/kalavai-client/issues) what engines you'd like to see.


> Kalavai is at a **very early stage** of its development. We encourage people to use it and give us feedback! Although we are trying to minimise breaking changes, these may occur until we have a stable version (v1.0).

## Want to know more?

- Get a free [Kalavai account](https://platform.kalavai.net) and access unlimited AI.
- Full [documentation](https://kalavai-net.github.io/kalavai-client/) for the project.
- [Join our Substack](https://kalavainet.substack.com/) for updates and be part of our community
- [Join our discord community](https://discord.gg/6VJWGzxg)


## Getting started

The `kalavai` CLI is the main tool to interact with the Kalavai platform, to create and manage both local and public pools. Let's go over its installation

<!--https://github.com/user-attachments/assets/af2ee15d-f18c-4802-8210-1873b0de07eb -->

### Requirements

- A laptop, desktop or Virtual Machine
- Admin / privileged access (eg. `sudo` access in linux or Administrator in Windows)
- Running Windows or Linux (see more details in our [compatibility matrix](#compatibility-matrix))


### Linux

Run the following command on your terminal:

```bash
curl -sfL https://raw.githubusercontent.com/kalavai-net/kalavai-client/main/assets/install_client.sh | bash -
```

### Windows

For Windows machines complete WSL configuration first before continuing. You must be running Windows 10 version 2004 and higher (Build 19041 and higher) or Windows 11 to use the commands below. **If you are on earlier versions** please see the [manual install](https://learn.microsoft.com/en-us/windows/wsl/install-manual) page.

1. Open a PowerShell with administrative permissions (_Run as Administrator_)

2. Install WSL2:
```bash
wsl --install -d Ubuntu-24.04
```

3. Make sure to enable `systemd` by editing (or creating if required) a file `/etc/wsl.conf`
```bash
[boot]
systemd=true
```

4. Restart the WSL instance by exiting and logging back in:
```bash
exit
wsl --shutdown
wsl -d Ubuntu-24.04
```

5. Inside WSL, install Kalavai:
```bash
curl -sfL https://raw.githubusercontent.com/kalavai-net/kalavai-client/main/assets/install_client.sh | bash -
```

**Note**: you **must keep the WSL console window open** to continue to share resources with an AI pool. If you restart your machine or close the console, you will need to resume kalavai as follows:
```bash
kalavai pool resume
```

**Known issue**: if the above resume command hangs or fails, try to run the pause command before and then reattempt resuming:
```bash
kalavai pool pause
kalavai pool resume
```

## Public pools: crowdsource community resources

This is the **easiest and most powerful** way to experience Kalavai. It affords users the full resource capabilities of the community and access to all its deployed LLMs, via an [OpenAI-compatible endpoint](https://kalavai-net.github.io/kalavai-client/public_llm_pool/#single-api-endpoint) as well as a [UI-based playground](https://kalavai-net.github.io/kalavai-client/public_llm_pool/#ui-playground).

Check out [our guide](https://kalavai-net.github.io/kalavai-client/public_llm_pool/) on how to join and start deploying LLMs.


## Createa a local, private pool

Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you wish to join computers in different locations / networks, check [managed kalavai](#public-pools-crowdsource-community-resources).

### 1. Start a seed node

Simply use the CLI to start your seed node:

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


## What next?

Within a pool, you can monitor the nodes connected and the resources available:

```bash
# Get all connected nodes
kalavai node list

# Get all resources within the pool (CPUs, RAM, GPUs...)
kalavai pool resources

# Get GPUs
kalavai pool gpus
```

### Enough already, let's run stuff!

Check our [examples](examples/) to put your new AI pool to good use!
- [Single node vLLM GPU LLM](examples/singlenode_gpu_vllm.md) deployment
- [Multi node vLLM GPU LLM](examples/multinode_gpu_vllm.md) deployment
- [Aphrodite-engine quantized LLM](examples/quantized_gpu_llm.md) deployment, including Kobold interface
- [Ray cluster](examples/ray_cluster.md) for distributed computation.


## Compatibility matrix

If your system is not currently supported, [open an issue](https://github.com/kalavai-net/kalavai-client/issues) and request it. We are expanding this list constantly.

### OS compatibility

Currently compatible and tested OS:
- Ubuntu (22.04, 24.04)
- Pop! OS 22.04
- Windows 10+ (using WSL2)

Currently compatible (untested. [Interested in testing them?](mailto:info@kalavai.net)):
- Debian-based linux
- Fedora
- RedHat
- Any distro capable of installing `.deb` and `.rpm` packages.

Currently not compatible:
- MacOS

### Hardware compatibility:
- `amd64` or `x86_64` CPU architecture
- (optional) NVIDIA GPU
- AMD and Intel GPUs are currently not supported (yet!)


## Roadmap

- [x] Kalavai client on Linux
- [x] [TEMPLATE] Distributed LLM deployment
- [x] Kalavai client on Windows (with WSL2)
- [x] Public pools
- [x] Collaborative LLM deployment
- [ ] [TEMPLATE] Distributed LLM fine tuning
- [ ] Kalavai client on Mac
- [x] Ray cluster support

Anything missing here? Give us a shout in the [discussion board](https://github.com/kalavai-net/kalavai-client/discussions)


## Contribute

- PR welcome!
- [Join the community](https://github.com/kalavai-net/kalavai-client/) and share ideas!
- Report [bugs, issues and new features](https://github.com/kalavai-net/kalavai-client/issues).
- Help improve our [compatibility matrix](#compatibility-matrix) by testing on different operative systems.
- [Community integrations](templates/README.md) are template jobs built by Kalavai and the community that makes deploying distributed workflows easy for users. Anyone can extend them and contribute to this repo.
- [Join our mailing list](http://eepurl.com/iC89hk) for release updates and priority access to new features!

### Star History

[![Star History Chart](https://api.star-history.com/svg?repos=kalavai-net/kalavai-client&type=Date)](https://star-history.com/#kalavai-net/kalavai-client&Date)


## Build from source

### Requirements

Python version <= 3.10.

On Ubuntu:

```bash
virtualenv -p python3 env
source env/bin/activate
sudo apt install python3-tk python3-dev rpm squashfs-tools ruby-dev build-essential gcc -y
sudo gem i fpm -f
pip install -e .
```

### Build

Run the build process with:
```bash
bash build.sh
```

This will produce two main assets:
- `dist/kalavai` as the linux executable CLI application
- `packages/kalavai-cli-*` for all compatible package installables.


### Unit tests

To run the unit tests, use:

```bash
python -m unittest
```
