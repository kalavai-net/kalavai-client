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


### Requirements to run the client

- Python 3.6+
- For seed and workers: Docker engine installed (for [linux](https://docs.docker.com/engine/install/ubuntu/), [Windows and MacOS](https://docs.docker.com/desktop/)) with [privilege access](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities).


### Install the client

The client is a python package and can be installed with one command:

```bash
pip install kalavai-client
```


## Createa a local, private LLM pool

> Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you are interested in join computers in different locations / networks, [contact us](mailto:info@kalavai.net) or [book a demo](https://app.onecal.io/b/kalavai/book-a-demo) with the founders.

You can create and manage your pools with the new kalavai GUI, which can be started with:

```bash
$ kalavai gui start

[+] Running 1/1
 ✔ Container kalavai_gui  Started0.1s  
Loading GUI, may take a few minutes. It will be available at http://localhost:3000
```

This will expose the GUI and the backend services in localhost. By default, the GUI is accessible via [http://localhost:3000](http://localhost:3000)

Note that to use the GUI you will need a free account in the platform. [Create one here](https://platform.kalavai.net).


### 1. Create an LLM pool

After you have logged in with your account, you can create your LLM pool by clicking on the `circle-plus` button. Give the pool a name, and select an IP to use as the pool address. Note that this address will need to be visible by worker machines that want to join in.

![Create an LLM pool](/docs/docs/assets/images/ui_create_cluster.png)


### 2. Add worker nodes

> **Important: only nodes within the same network as the seed node (the one that created the pool) can be added successfully. If you are interested in join computers in different locations / networks, [contact us](mailto:info@kalavai.net) or [book a demo](https://app.onecal.io/b/kalavai/book-a-demo) with the founders.**

Increase the power of your AI pool by inviting others to join. For that, you need to generate a joining token. Use the navigation panel to go to `Devices`, and then click the `circle-plus` button to add new devices. You can select the `Access mode`, which determine the level of access new nodes will have over the pool:
- `admin`: Same level of access than the seed node, including generating new joining tokens and deleting nodes.
- `user`: Can deploy jobs, but lacks admin access over nodes.
- `worker`: Workers carry on jobs, but cannot deploy their own jobs.

![Invite others to join](/docs/docs/assets/images/ui_devices_invite.png)

Copy the joining token and share it with others. On the machines you want to add to the pool, after logging in to kalavai GUI, paste the joining token in the text field under `Access with token`, and click join

![Use the token to join](/docs/docs/assets/images/ui_join_part1.png)

Kalavai asks you if you want to join (run workloads in the local machine) or attach (use the node to access and control the pool, without running workloads) to the pool. 

![Choose to join or attach](/docs/docs/assets/images/ui_join_part2.png)


### 3. Explore resources

For both seed and worker nodes, the dashboard shows a high level view of the LLM pool: resources available, current utilisation and active devices and deployments.

![Dashboard](/docs/docs/assets/images/ui_dashboard_multiple.png)

Use the navigation bar to see more details on key resources:

- **Devices**: every machine connected to the pool and its current status

![Devices](/docs/docs/assets/images/ui_all_devices.png)

- **GPUs**: list of all available and utilised GPUs

![GPUs](/docs/docs/assets/images/ui_all_gpus.png)

- **Jobs**: all models and deployments active in the pool

![Deployments](/docs/docs/assets/images/ui_monitor_jobs.png)


### 4. Leave the pool

Any device can leave the pool at any point and its workload will get reassigned. To leave the pool, click the `circle-stop` button on the dashboard, under `Local status` card. Nodes can rejoin at any point [following the above procedure](#2-add-worker-nodes).

![Leave the pool](/docs/docs/assets/images/ui_leave_pool.png)

## What's next

Now that you know how to get a pool up and running, check our [end to end tutorial](./self_hosted_llm_pool.md) on how to self-host an LLM Pool, or go full on easy-mode by [joining a public pool](public_llm_pool.md).
