![alt text](docs/docs/assets/icons/logo_no_background.png)

# Turn everyday devices into your own AI cluster

> Kalavai is a self-hosted platform that turns **everyday devices** into your very own AI cluster. Do you have an old desktop or a gaming laptop gathering dust? Aggregate resources from multiple machines and **say goodbye to CUDA out of memory errors**. Deploy your favourite open source LLM, fine tune it with your own data, or simply run your distributed work, zero-devops. **Simple. Private. Yours.**

This repository contains:
- Releases of our [free CLI](#install): turn your devices into AI-capable servers.
- [Community integrations](templates/README.md): template jobs built by Kalavai and the community that makes deploying distributed workflows easy for users.
- Full [documentation](https://kalavai-net.github.io/kalavai-client/) (WIP) for the project.

[Join our mailing list](http://eepurl.com/iC89hk) for release updates and priority access to new features!


## Install

### Requirements

- A laptop, desktop or Virtual Machine
- Fast internet connection (50+ Mbps recommended, but can run on slower connections).
- Admin / privileged access (eg. `sudo` access in linux)
- Runining a compatible Operative system (see [compatibility matrix](#compatibility-matrix))


### One-line installer

To install the kalavai CLI, run the following command:

```bash
curl -sfL https://raw.githubusercontent.com/kalavai-net/kalavai-client/main/installer/install_client.sh | bash -
```

#### `kalavai` CLI

Manage your AI cluster or deploy and monitor jobs with the `kalavai` CLI:

```bash
$ kalavai --help

usage: cli.py [-h] command ...

positional arguments:
  command
    start        Start Kalavai cluster and start/resume sharing resources.
    token        Generate a join token for others to connect to your cluster
    join         Join Kalavai cluster and start/resume sharing resources.
    stop         Stop sharing your device and clean up. DO THIS ONLY IF YOU WANT TO REMOVE KALAVAI-CLIENT from your
                 device.
    pause        Pause sharing your device and make your device unavailable for kalavai scheduling.
    resume       Resume sharing your device and make device available for kalavai scheduling.
    resources    Display information about resources on the cluster
    nodes        Display information about nodes connected
    diagnostics  Run diagnostics on a local installation of kalavai, and stores in log file
    job

options:
  -h, --help  show this help message and exit
```

To get started, check our [quick start](#quick-start) guide.


## How it works?

To create an AI cluster, you need a **seed node** which acts as a control plane. It handles bookkeeping for the cluster. With a seed node, you can generate join tokens, which you can share with other machines --**worker nodes**.

The more worker nodes you have in a cluster, the bigger workloads it can run. _Note that the only requirement for a fully functioning cluster is a single seed node._

Once you have a cluster running, you can easily deploy workloads using [template jobs](templates/README.md). These are community integrations that let users deploy jobs, such as LLM deployments or LLM fine tuning. A template makes using Kalavai really easy for end users, with a parameterised interface, and it also makes the **platform infinitely expandable**.

## Quick start

Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you wish to join computers in different locations / networks, check our [managed kalavai](#managed-kalavai) offering.

### Create a seed node

#### Self-hosted Kalavai

Simply use the CLI to start your seed node:

```bash
kalavai start
```

Note that it will take a few minutes to setup and download all dependencies. Check the status of your cluster with:

```bash
kalavai diagnostics
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
kalavai token
```

Copy the displayed token. On the worker node, run:

```bash
kalavai join <token>
```

After some time, you should be able to see the new node:

```bash
kalavai nodes
```

You can also see the total resources available:

```bash
kalavai resources
```

### Enough already, let's run stuff!

In short, run a template job:

```bash
kalavai run <template name> --values-path <values file>
```

Each job requires two values:
- Name of the template --get a list of available integrations with `kalavai templates`
- Parameter values for the template.

Here we will use the example of deploying a LLM (vllm template). To generate default values file:
```bash
kalavai job defaults vllm > values.yaml
```

This will create a `values.yaml` file that contains the default values for a vllm job, such as the model id, the number of workers, etc.

Then you can use the newly created values to run the job:
```bash
kalavai job run vllm --values-path values.yaml
```

In this case, the job also deploys a service that can be accessible via an endpoint. Find out the url with:

```bash
$ kalavai job list 

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Deployment        ┃ Status                            ┃ Endpoint               ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ vllm-deployment-1 │ Available: All replicas are ready │ http://100.8.0.2:31992 │
└───────────────────┴───────────────────────────────────┴────────────────────────┘
```

Kalavai creates an endpoint for each deployed job, which is displayed above. In the case of vLLM jobs, this is a model endpoint that can be interacted as you would any [LLM server](https://docs.vllm.ai/en/latest/getting_started/quickstart.html#using-openai-completions-api-with-vllm). See the [vLLM template documentation](templates/vllm/README.md) for info on how to interact with the model, but as a quick go:
```bash
curl http://100.8.0.2:31992/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "facebook/opt-350m",
        "prompt": "San Francisco is a",
        "max_tokens": 7,
        "temperature": 0
    }'
```

For more information on what a template can do:
```bash
kalavai job describe vllm
```

Job monitoring and lifecycle using the name of the deployment above:
```bash
# provide the logs of a specific job
$ kalavai job logs vllm-deployment-1

Loading pt checkpoint shards: 100% Completed | 1/1 [00:00<00:00,  2.77it/s]                           
           Loading pt checkpoint shards: 100% Completed | 1/1 [00:00<00:00,  2.77it/s]                           

           INFO 09-24 01:01:10 model_runner.py:1008] Loading model weights took 0.6178 GB
           ...
           INFO:     Started server process [548]                                                            
           INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)                               
           INFO 09-24 01:01:21 metrics.py:351] Avg prompt throughput: 0.0 tokens/s, Avg generation               
           throughput: 0.0 tokens/s, Running: 0 reqs, Swapped: 0 reqs, Pending: 0 reqs, GPU KV cache             
           usage: 0.0%, CPU KV cache usage: 0.0%.
```

Once you no longer need the job, you can delete it:

```bash
# delete a job
kalavai job delete vllm-deployment-1
```

To find out more about templates, check out our [documentation](templates/README.md).


## Compatibility matrix

If your system is not currently supported, [open an issue](https://github.com/kalavai-net/kalavai-client/issues) and request it. We are expanding this list constantly.

### OS compatibility

Currently compatible and tested OS:
- Debian-based linux (such as Ubuntu)

Currently compatible (untested. [Interested in testing them?](mailto:info@kalavai.net)):
- Fedora
- RedHat
- Any distro capable of installing `.deb` and `.rpm` packages.

Coming soon:
- Windows 10+ with WSL

Currently not compatible:
- MacOS

### Hardware compatibility:
- `amd64` or `x86_64` CPU architecture
- (optional) NVIDIA GPU
- AMD and Intel GPUs are currently not supported (yet!)

## Contribute

- [Join in](https://github.com/kalavai-net/kalavai-client/discussions/1) and share ideas!
- Report [bugs, issues and new features](https://github.com/kalavai-net/kalavai-client/issues).
- Help improve our [compatibility matrix](#compatibility-matrix) by testing on different operative systems.
- Develop and contribute new [templates](templates/README.md)
- [Join our mailing list](http://eepurl.com/iC89hk) for release updates and priority access to new features!
