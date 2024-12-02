---
tags:
  - quickstart
---

# Quickstart

For this guide we assume you have either a compatible linux machine or WSL running on windows. For more info, check our [getting started](getting_started.md) guide.

Goal: to get you up and running as fast and painlessly as possible, from zero to distributed LLM deployment across community devices.


## 1. Download Kalavai

Download and install the latest version of `kalavai`:

```bash
curl -sfL https://raw.githubusercontent.com/kalavai-net/kalavai-client/main/assets/install_client.sh | bash -
```

## 2. Create a free account

Go to [our platform](https://platform.kalavai.net) and register to get an account. You'll need the credentials later.

## 3. Join a public computing pool

Computing pools are the heart and soul of Kalavai. It's a shared space where developers, researchers and enthusiasts join in with their computing power for the benefit of the community, so each user can go beyond the hardware they own.

In the platform, go to `Computing Pools` and click `JOIN` on any of the pools shown. This will display the details on how to join using the `kalavai` client.

![Public pools](/docs/docs/assets/images/public_seeds.png)


Paste the command and run it in your computer. After a few minutes you should be connected and ready to deploy!

```bash
$ kalavai pool join <join token>

[01:24:45] Token format is correct                                                                                                                               
[sudo] password for carlosfm: 
[01:24:48] Joining private network                                                                                                                               
[KalavaiAuthClient]Logged in as carlosfm
[01:25:01] Scanning for valid IPs...  
           Using 100.10.0.7 address for worker    
            Connecting to publicllm @ 100.10.0.2 (this may take a few minutes)...
            You are connected to publicllm
```

## 4. Deploy an LLM

We are now ready to deploy an LLM across the available resources. First, let's check what resources are available:

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

OK, let's deploy! We are going to deploy Qwen2.5-1.5B-Instruct model across 2 machines. We have already prepared a config file for it [here](/templates/aphrodite/examples/qwen2.5-1.5B.yaml). 

With `kalavai`, you can deploy most LLMs using vLLM or Aphrodite-Engine, with one command, passing all the parameter details within the config file. The `run` command asks you whether you want to target or avoid certain GPU models; for now, we'll just select `0`, which will use any GPU available.

```bash
$ kalavai job run aphrodite --values qwen2.5-1.5B.yaml

[01:42:07] SELECT Target GPUs for the job          
[KalavaiAuthClient]Logged in as carlosfm

0) Any/None
1) NVIDIA-NVIDIA GeForce RTX 2070 (8GB) (in use: False)
2) NVIDIA-NVIDIA GeForce RTX 3060 (12GB) (in use: False)
3) NVIDIA-NVIDIA GeForce RTX 3050 Ti Laptop GPU (4GB) (in use: False)
-->  : 0

[01:42:40] AVOID Target GPUs for the job

0) Any/None
1) NVIDIA-NVIDIA GeForce RTX 2070 (8GB) (in use: False)
2) NVIDIA-NVIDIA GeForce RTX 3060 (12GB) (in use: False)
3) NVIDIA-NVIDIA GeForce RTX 3050 Ti Laptop GPU (4GB) (in use: False)
-->  : 0

[01:43:13] Template /home/carlosfm/.cache/kalavai/templates/aphrodite/template.yaml successfully deployed!
[01:43:15] Service deployed   
```

## 5. Calling the model

Deploying a model could take several minutes, since we are provisioning the machines, downloading the model and loading it in memory. To check the progress, run the following:

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

Once all workers are in the `Running` state, check the model is ready for inference:

```bash
$ kalavai job logs qwen-1 qwen-1-ps-0


```

 There are various ways to do so, but for this tutorial we'll use the KoboldAI launched with Aphrodite-Engine. You can see the endpoint by running `kalavai job list`. In our example: http://100.10.0.2:32136



