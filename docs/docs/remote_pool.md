---
tags:
  - remote connection
---

# Connecting to a remote pool

You can connect to a remote pool too. First, get the connection credentials from the seed node:

```bash
kalavai pool connection
```

Then, in the remote machine, use those credentials to connect:

```bash
kalavai pool connect <KALAVAI_API_URL> <API_KEY>
```

Now the local machine can use the [CLI](cli.md) and the [GUI](gui.md) to send commands to the remote pool
