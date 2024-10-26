![alt text](docs/docs/assets/icons/logo_no_background.png)

<div align="center">

![GitHub Release](https://img.shields.io/github/v/release/kalavai-net/kalavai-client) ![GitHub download count](https://img.shields.io/github/downloads/kalavai-net/kalavai-client/total
) ![GitHub contributors](https://img.shields.io/github/contributors/kalavai-net/kalavai-client) ![GitHub License](https://img.shields.io/github/license/kalavai-net/kalavai-client) ![GitHub Repo stars](https://img.shields.io/github/stars/kalavai-net/kalavai-client) [![Discord](https://img.shields.io/discord/1295009828623880313?logo=discord&label=discord)](https://discordapp.com/channels/1295009828623880313)

</div>

# Turn everyday devices into your own AI cluster

> Kalavai is an **open source, self-hosted** platform that turns **everyday devices** into your very own AI cluster. Home desktops, gaming laptops, work computers, cloud VMs...Aggregate resources from multiple machines and **say goodbye to CUDA out of memory errors**. Deploy your favourite open source LLM, fine tune it with your own data, or simply run your distributed work, zero-devops. **Simple. Private. Yours.**

![Overview of Kalavai](/docs/docs/assets/images/overview_diagram.png)

This repository contains:
- Our [open, free CLI](#install): turn your devices into AI-capable servers.
- [Community integrations](templates/README.md): template jobs built by Kalavai and the community that makes deploying distributed workflows easy for users.
- Full [documentation](https://kalavai-net.github.io/kalavai-client/) (WIP) for the project.
- Our [community discussions](https://github.com/kalavai-net/kalavai-client/discussions) hub.

[Join our mailing list](http://eepurl.com/iC89hk) for release updates and priority access to new features!

## What can Kalavai do?

Kalavai is a platform for distributed computing, and thus it supports a wide range of tasks. Here is a growing list of examples:
- [Single node vLLM GPU LLM](examples/singlenode_gpu_vllm.md) deployment
- [Multi node vLLM GPU LLM](examples/multinode_gpu_vllm.md) deployment
- [Aphrodite-engine quantized LLM](examples/quantized_gpu_llm.md) deployment, including Kobold interface
- [Ray cluster](examples/ray_cluster.md) for distributed computation.


## Install

> Kalavai is at a **very early stage** of its development. We encourage people to use it and give us feedback! Although we are trying to minimise breaking changes, these may occur until we have a stable version (v1.0).

https://github.com/user-attachments/assets/af2ee15d-f18c-4802-8210-1873b0de07eb



### Requirements

- A laptop, desktop or Virtual Machine
- Admin / privileged access (eg. `sudo` access in linux or Administrator in Windows)
- Running Windows or Linux (see more details in our [compatibility matrix](#compatibility-matrix))

Check out the details on all [compatible systems](#compatibility-matrix).


### Linux

To install the `kalavai` CLI, run the following command on your terminal:

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

**Note**: you **must keep the WSL console window open** to continue to share resources with an AI cluster. If you restart your machine or close the console, you will need to resume kalavai as follows:
```bash
kalavai cluster resume
```

**Known issue**: if the above resume command hangs or fails, try to run the pause command before and then reattempt resuming:
```bash
kalavai cluster pause
kalavai cluster resume
```

To make sure the agent is running, check the diagnostics:
```bash
$ kalavai cluster diagnostics

App installed: True                                   cli.py:531
Agent running: True                                   cli.py:531
Containerd running: True                              cli.py:531

Getting deployment status...  
...
```



### What's next

You are ready to create and join clusters! To get your hands dirty, check our [quick start](#quick-start) guide.

```bash
$ kalavai --help

usage: cli.py [-h] command ...

positional arguments:
  command
    login     (For public clusters only) Log in to Kalavai server.
    logout    (For public clusters only) Log out of Kalavai server.
    cluster
    node
    job
    ray

options:
  -h, --help  show this help message and exit
```


## How it works?

To create an AI cluster, you need a **seed node** which acts as a control plane. It handles bookkeeping for the cluster. With a seed node, you can generate join tokens, which you can share with other machines --**worker nodes**.

The more worker nodes you have in a cluster, the bigger workloads it can run. _Note that the only requirement for a fully functioning cluster is a single seed node._

Once you have a cluster running, you can easily deploy workloads using [template jobs](templates/README.md). These are community integrations that let users deploy jobs, such as LLM deployments or LLM fine tuning. A template makes using Kalavai really easy for end users, with a parameterised interface, and it also makes the **platform infinitely expandable**.

## Cluster quick start

Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you wish to join computers in different locations / networks, check our [managed kalavai](#managed-kalavai) offering.

### Create a seed node

#### Self-hosted Kalavai

Simply use the CLI to start your seed node:

```bash
kalavai cluster start <cluster-name>
```

Note that it will take a few minutes to setup and download all dependencies. Check the status of your cluster with:

```bash
kalavai cluster diagnostics
```


#### Managed Kalavai

> Interested in a fully managed, hosted Kalavai server? [Register your interest](http://eepurl.com/iC89hk) and get on top of the list. _Note: the first 100 to register will get a massive discount!_

_Wait, isn't Kalavai free and runs on my computer? Why would I need a hosted solution?_ Kalavai offers a <ins>fully managed, hosted seed node(s)</ins>, so you can overcome some of the limitations of running it yourself. Use managed Kalavai if:
- Your devices are not in the same local network
- You want to access your cluster remotely
- You want a high availability cluster --no downtime!


### Add a worker node

In the seed node, generate a join token:
```bash
kalavai cluster token
```

Copy the displayed token. On the worker node, run:

```bash
kalavai cluster join <token>
```

Note that **worker nodes must be able to see the seed node**; this could be achieved using a public IP on the seed node or by having both computers on the same local network. After some time, you should be able to see the new node:

```bash
kalavai node list
```

You can also see the total resources available:

```bash
kalavai cluster resources
```

### Enough already, let's run stuff!

Check our [examples](examples/) to put your new AI cluster to good use!


## Compatibility matrix

If your system is not currently supported, [open an issue](https://github.com/kalavai-net/kalavai-client/issues) and request it. We are expanding this list constantly.

### OS compatibility

Currently compatible and tested OS:
- Debian-based linux (such as Ubuntu)
- Windows 10+ (using WSL2)

Currently compatible (untested. [Interested in testing them?](mailto:info@kalavai.net)):
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
- [ ] [TEMPLATE] Distributed LLM fine tuning
- [ ] Kalavai client on Mac
- [ ] Ray cluster support

Anything missing here? Give us a shout in the [discussion board](https://github.com/kalavai-net/kalavai-client/discussions)


## Contribute

- PR welcome!
- [Join the community](https://github.com/kalavai-net/kalavai-client/) and share ideas!
- Report [bugs, issues and new features](https://github.com/kalavai-net/kalavai-client/issues).
- Help improve our [compatibility matrix](#compatibility-matrix) by testing on different operative systems.
- Develop and contribute new [templates](templates/README.md)
- [Join our mailing list](http://eepurl.com/iC89hk) for release updates and priority access to new features!


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
