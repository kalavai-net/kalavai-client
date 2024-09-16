---
tags:
  - join
  - worker node
---

# Join an existing AI cluster

## Requirements

* Worker nodes should be able to connect directly to the master node (either via public IP or within the same private network)

## Install Kalavai client app

See [how to install kalavai client app](install_client.md)

## Join the cluster

Fetch the joining token from the master node:
```bash
kalavai generate-token
```

And then join!
Create cluster:
```bash
kalavai join ---
```

## What's next?

Your cluster will now be able to schedule workloads on the new node. Check out the [app integrations](install_apps.md) for more info.
