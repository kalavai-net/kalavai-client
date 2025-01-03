![alt text](docs/docs/assets/icons/logo_no_background.png)

<div align="center">

![GitHub Release](https://img.shields.io/github/v/release/kalavai-net/kalavai-client) ![GitHub download count](https://img.shields.io/github/downloads/kalavai-net/kalavai-client/total
) ![GitHub contributors](https://img.shields.io/github/contributors/kalavai-net/kalavai-client) ![GitHub License](https://img.shields.io/github/license/kalavai-net/kalavai-client) ![GitHub Repo stars](https://img.shields.io/github/stars/kalavai-net/kalavai-client) [![Discord](https://img.shields.io/discord/1295009828623880313?logo=discord&label=discord)](https://discordapp.com/channels/1295009828623880313) [![Signup](https://img.shields.io/badge/Kalavai-Signup-brightgreen)](https://platform.kalavai.net)

`⭐ Kalavai is open-source - Support us by leaving a star ⭐`

</div>


# Kalavai: the first platform to crowdsource AI computation

### Run large AI projects that you couldn't with your own hardware alone

> Kalavai is an **open source** platform that turns **everyday devices** into your very own AI supercomputer. We help you aggregate resources from multiple machines: home desktops, gaming laptops, work computers, cloud VMs... When you need to **go beyond**, Kalavai **facilitates matchmaking** of resources so anyone in our community can tap into a larger pool of devices by **inspiring others to join** your cause.

<div align="center">

<a href="https://www.producthunt.com/products/kalavai/reviews?utm_source=badge-product_review&utm_medium=badge&utm_souce=badge-kalavai" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/product_review.svg?product_id=720725&theme=neutral" alt="Kalavai - The&#0032;first&#0032;platform&#0032;to&#0032;crowdsource&#0032;AI&#0032;computation | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

</div>

![Overview of Kalavai](/docs/docs/assets/images/overview_diagram.png)

## What can Kalavai do?

Kalavai's goal is to make AI hardware accessible and affordable to all. We do it in two ways:

1. The open source version can be used to pool any devices, for _commercial and non-commercial_ purposes. This is perfect as **a management layer for research groups and organisations** that already have hardware lying around and wish to unlock its power, without requiring a devops team. This AI pools are free, secure and totally private.

2. Our [managed version](https://platform.kalavai.net) acts as a **platform to crowdsource AI computing between its members**, facilitating users to connect with the community's resources. _Think Reddit, but instead of memes, users share resources with inspiring projects._

Both versions can be managed using our free [kalavai CLI](#getting-started) tool.

> Kalavai is at a **very early stage** of its development. We encourage people to use it and give us feedback! Although we are trying to minimise breaking changes, these may occur until we have a stable version (v1.0).


### Want to know more?

- Get a free [Kalavai account](https://platform.kalavai.net) and access unlimited AI.
- Full [documentation](https://kalavai-net.github.io/kalavai-client/) for the project.
- [Join our Substack](https://kalavainet.substack.com/) for updates and be part of our community


### News updates

- 23 December 2024: Release of [public petals swarm](/docs/docs/petals.md)
- 24 November 2024: Common pools with private user spaces
- 31 October 2024: [Help needed](https://kalavainet.substack.com/p/llm-world-record-testing-the-waters) to test public pools!
- 30 October 2024: Release of our [public pool platform](https://platform.kalavai.net)
- 22 October 2024: Announcement of our [world record largest distributed LLM inference](https://kalavainet.substack.com/p/setting-a-new-world-record-the-worlds)



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


## Createa a local pool

Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you wish to join computers in different locations / networks, check [managed kalavai](#public-pools-crowdsource-community-resources).

### 1. Start a seed node

Simply use the CLI to start your seed node:

```bash
kalavai pool start <pool-name>
```

Now you are ready to add worker nodes to this seed. To do so, generate a joining token:
```bash
$ kalavai pool token

Join token: <token>
```

### 2. Add worker nodes

Increase the power of your AI pool by inviting others to join.

Copy the joining token. On the worker node, run:

```bash
kalavai pool join <token>
```


## Public pools: crowdsource community resources

Our public platform expands local pools in two key aspects:
- Worker nodes **no longer have to be in the same local network**
- Users can **tap into community resources**: inspire others in the community to join their projects with their resources

To get started, you need is a [free account on our platform](https://platform.kalavai.net).


### A) Tap into community resources

Create a new pool, using a public location provided by Kalavai:
```bash
# Authenticate with your kalavai account
kalavai login

# Get available public locations
kalavai location list

┏━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓  
┃ VPN ┃ location    ┃ subnet        ┃          
┡━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ 0   │ uk_london_1 │ 100.10.0.0/16 │
└─────┴─────────────┴───────────────┘

# Create and publish your pool
kalavai pool start <pool-name> --location uk_london_1
```

If all goes well, your pool will be created and published on the `Public Seeds` section of our [platform](https://platform.kalavai.net)

![Public seeds](/docs/docs/assets/images/public_seeds.png)

Note: to be able to publish pools your account needs to have sufficient karma points. Earn karma by [sharing your resources](#b-share-resources-with-inspiring-community-projects) with others.


### B) Share resources with inspiring community projects

Have idle computing resources? Wish to be part of exciting public projects? Want to give back to the community? Earn social credit (both literally and metaphorically) by sharing your computer with others within the community.

All you need is a public joining key. Get them in our platform, on the list of published pools. Press `Join` and follow the instructions

![alt text](/docs/docs/assets/images/join_public_pool.png)


## What next?

Within a pool, you can monitor the nodes connected and the resources available:

```bash
# Get all connected nodes
kalavai node list

# Get all resources within the pool (CPUs, RAM, GPUs...)
kalavai pool resources
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
