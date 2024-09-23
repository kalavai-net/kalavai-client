---
tags:
  - kalavai-client
  - cli
  - install
  - requirements
  - quick start
---

# Quick start

Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you wish to join computers in different locations / networks, check our [managed kalavai](#managed-kalavai) offering.

### Create a seed node

Simply use the CLI to start your seed node:

```bash
kalavai start
```

Note that it will take a few minutes to setup and download all dependencies. Check the status of your cluster with:

```bash
kalavai diagnostics
```

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
kalavai job list 
```

Job monitoring and lifecycle:
```bash
# provide the logs of a specific job
kalavai job logs <name of the job> 
# delete a job
kalavai job delete <name of the job>
```
