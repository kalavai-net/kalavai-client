---
tags:
  - remote connection
---

# Connecting to a remote pool

You can connect to a remote pool too. First, get the connection credentials from the seed node:

```bash
kalavai pool credentials
```

This command shows how to connect a remote machine to the local pool.

```
Kalavai API URL: http://<ip address>:49152
Kalavai API Key: be416a3e-5aa3-47e3-8398-0f993518f3dc

Run the following command from a remote machine to connect to this pool:

kalavai pool connect http://<ip address>:49152 be416a3e-5aa3-47e3-8398-0f993518f3dc
```


Then, in the remote machine, use those credentials to connect:

```bash
kalavai pool connect <KALAVAI_API_URL> <API_KEY>
```

Now the local machine can use the [CLI](cli.md) and the [GUI](gui.md) to send commands to the remote pool
