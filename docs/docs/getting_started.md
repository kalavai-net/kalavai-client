---
tags:
  - kalavai-client
  - cli
  - install
  - requirements
---

# Getting started

Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you wish to join computers in different locations / networks, check our [managed kalavai](#managed-kalavai) offering.

The `kalavai` CLI is the main tool to interact with the Kalavai platform, to create and manage both local and public pools. Let's go over its installation

<!--https://github.com/user-attachments/assets/af2ee15d-f18c-4802-8210-1873b0de07eb -->

## Requirements

- A laptop, desktop or Virtual Machine
- Admin / privileged access (eg. `sudo` access in linux or Administrator in Windows)
- Running Windows or Linux (see more details in our [compatibility matrix](./compatibility.md))


## Linux

Run the following command on your terminal:

```bash
curl -sfL https://raw.githubusercontent.com/kalavai-net/kalavai-client/main/assets/install_client.sh | bash -
```

## Windows

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


### Hardware compatibility:
- `amd64` or `x86_64` CPU architecture
- (optional) NVIDIA GPU
- AMD and Intel GPUs are currently not supported (yet!)



## What's next

Now that you have your client up and running, you are ready to [create](local_pool.md) and join computing pools. The easiest way to get started is by [joining a public pool](public_pool.md), so we'll look at that next. 