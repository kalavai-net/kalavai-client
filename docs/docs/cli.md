---
tags:
  - cli
  - command line
---

# Kalavai from the command line (CLI)

The full functionality set of Kalavai LLM Pools can be accessed via the command line. This is ideal when working with Virtual Machines in the cloud or in automating workflows where GUI access is not possible or not required.

## Requirements

Make sure you have the kalavai-client installed in your machine before continuing.

## Overview

```bash
$ kalavai --help

usage: kalavai [-h] command ...

positional arguments:
  command
    login     [AUTH] (For public clusters only) Log in to Kalavai server.
    logout    [AUTH] (For public clusters only) Log out of Kalavai server.
    gui
    location
    pool
    storage
    node
    job
    ray

options:
  -h, --help  show this help message and exit
```

For help on a specific command, or group of commands, you can use the --help flag:
```bash
$ kalavai pool --help

usage: kalavai pool [-h] command ...

positional arguments:
  command
    publish      [AUTH] Publish pool to Kalavai platform, where other users may be able to join
    unpublish    [AUTH] Unpublish pool to Kalavai platform. Cluster and all its workers will still work
    list         [AUTH] List public pools in to Kalavai platform.
    start        Start Kalavai pool and start/resume sharing resources.
    token        Generate a join token for others to connect to your pool
    check-token  Utility to check the validity of a join token
    join         Join Kalavai pool and start/resume sharing resources.
    stop         Stop sharing your device and clean up. DO THIS ONLY IF YOU WANT TO REMOVE KALAVAI-CLIENT from your
                 device.
    pause        Pause sharing your device and make your device unavailable for kalavai scheduling.
    resume       Resume sharing your device and make device available for kalavai scheduling.
    gpus         Display GPU information from all connected nodes
    resources    Display information about resources on the pool
    update       Update kalavai pool
    status       Run diagnostics on a local installation of kalavai
    attach       Set creds in token on the local instance

options:
  -h, --help     show this help message and exit
```

## Examples

### Start a seed node and get token

```bash
kalavai pool start <pool-name>
```

Now you are ready to add worker nodes to this seed. To do so, generate a joining token:
```bash
$ kalavai pool token --user

Join token: <token>
```

### Add worker nodes


```bash
kalavai pool join <token>
```

### Check resources in the pool

List resources are available:

```bash
$ kalavai pool resources

┏━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃           ┃ n_nodes ┃ cpu   ┃ memory      ┃ nvidia.com/gpu ┃
┡━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Available │ 4       │ 38.08 │ 70096719872 │ 3              │
├───────────┼─────────┼───────┼─────────────┼────────────────┤
│ Total     │ 4       │ 42    │ 70895734784 │ 3              │
└───────────┴─────────┴───────┴─────────────┴────────────────┘

$ kalavai pool gpus

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┓
┃ Node               ┃ Ready ┃ GPU(s)                                               ┃ Available ┃ Total ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━┩
│ carlosfm-desktop-1 │ True  │ NVIDIA-NVIDIA GeForce RTX 2070 (8 GBs)               │ 1         │ 1     │
├────────────────────┼───────┼──────────────────────────────────────────────────────┼───────────┼───────┤
│ carlosfm-desktop-2 │ True  │ NVIDIA-NVIDIA GeForce RTX 3060 (12 GBs)              │ 1         │ 1     │
├────────────────────┼───────┼──────────────────────────────────────────────────────┼───────────┼───────┤
│ pop-os             │ True  │ NVIDIA-NVIDIA GeForce RTX 3050 Ti Laptop GPU (4 GBs) │ 1         │ 1     │
└────────────────────┴───────┴──────────────────────────────────────────────────────┴───────────┴───────┘
```

### Inspect jobs deployed

List available jobs:

```bash
$ kalavai job list

┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Deployment ┃ Status                         ┃ Workers    ┃ Endpoint                ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ qwen-1     │ [2024-11-27T02:17:35Z] Pending │ Pending: 1 │ http://100.10.0.2:30271 │
│            │                                │ Ready: 1   │                         │
└────────────┴────────────────────────────────┴────────────┴─────────────────────────┘
[01:48:23] Check detailed status with kalavai job status <name of deployment> 
           Get logs with kalavai job logs <name of deployment> (note it only works when the deployment is complete) 
```
