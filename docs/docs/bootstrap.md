---
tags:
  - create cluster
  - bootstrap
  - master node
---

# Bootstrap a new AI cluster

Intro

## Requirements

At least 1 computer (master node)
Public IP (or all nodes within the same private network)
Unique hostnames


## Install the Kalavai client

See [how to install kalavai client](install_client.md)



## Bootstrap your master node


Once it's installed, run the CLI app with:

```bash
kalavai --help
```

```bash
usage: kalavai [-h] command ...

positional arguments:
  command
    login     Login with your Kalavai user email and password. Get an account from https://platform.kalavai.net
    logout    Logout from your kalavai user account.
    start     Join Kalavai cluster and start/resume sharing resources.
    status    Check the current status of your device.
    stop      Stop sharing your device and clean up. DO THIS ONLY IF YOU WANT TO REMOVE KALAVAI-CLIENT from your device.
    pause     Pause sharing your device and make your device unavailable for kalavai scheduling.

options:
  -h, --help  show this help message and exit
```

Create cluster:
```bash
kalavai start ---
```


C&P join token and use it on other nodes to [join the cluster](join.md)

## What's next

[Install your app integrations](install_apps.md) and use your cluster!
