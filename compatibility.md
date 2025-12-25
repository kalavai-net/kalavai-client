---
tags:
  - requirements
  - compatibility
---

# Compatibility matrix

If your system is not currently supported, [open an issue](https://github.com/kalavai-net/kalavai-client/issues) and request it. We are expanding this list constantly.


### OS compatibility

Currently **seed nodes** are supported exclusively on linux machines (x86_64 platform). However Kalavai supports mixed pools, i.e. having Windows and MacOS computers as workers.

Since **worker nodes** run inside docker, any machine that can run docker **should** be compatible with Kalavai. Here are instructions for [linux](https://docs.docker.com/engine/install/), [Windows](https://docs.docker.com/desktop/setup/install/windows-install/) and [MacOS](https://docs.docker.com/desktop/setup/install/mac-install/).

The kalavai client, which controls and access pools, can be installed on any machine that has python 3.10+.


### Hardware compatibility:

- `amd64` or `x86_64` CPU architecture for seed and worker nodes.
- `arm64` CPU architecture for worker nodes. Note: not all workloads support arm64 workers.
- NVIDIA GPU or AMD GPUs
- Mac M series and Intel GPUs are currently not supported ([interested in helping us test it?](https://kalavai-net.github.io/kalavai-client/compatibility/#help-testing-amd-gpus))


## Help testing new systems

If you want to help testing Kalavai in new Windows / Linux based systems (thank you!), follow the next steps:

1. Follow the [instructions](getting_started.md#install-the-client) to install the kalavai client.

2. Save the entire install logs (printed out in the console) to a file (install.log)

3. If the installation went through, run kalavai commands to test the output:
```bash
kalavai pool status > status.log
kalavai pool start test > test_pool.log
kalavai pool resources > resources.log
```

4. Create an [issue on our repo](https://github.com/kalavai-net/kalavai-client/issues) and share the results. Include the four log files (status.log, test_pool.log, resources.log and install.log) as well as a description of the system you are testing.

5. If the system ends up being supported, you'll be invited to create a PR to add support to the compatibility matrix.


