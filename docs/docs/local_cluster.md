---
tags:
  - create local cluster
  - bootstrap
  - seed node
---

## Createa a local cluster

Kalavai is **free to use, no caps, for both commercial and non-commercial purposes**. All you need to get started is one or more computers that can see each other (i.e. within the same network), and you are good to go. If you wish to join computers in different locations / networks, check [managed kalavai](#public-clusters-crowdsource-community-resources).

### 1. Start a seed node

Simply use the CLI to start your seed node:

```bash
kalavai cluster start <cluster-name>
```

Now you are ready to add worker nodes to this seed. To do so, generate a joining token:
```bash
$ kalavai cluster token

Join token: <token>
```

### 2. Add worker nodes

Increase the power of your AI cluster by inviting others to join.

Copy the joining token. On the worker node, run:

```bash
kalavai cluster join <token>
```