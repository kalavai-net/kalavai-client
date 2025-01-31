---
tags:
  - requirements
  - compatibility
---

# Compatibility matrix

If your system is not currently supported, [open an issue](https://github.com/kalavai-net/kalavai-client/issues) and request it. We are expanding this list constantly.


### OS compatibility

Since **worker nodes** run inside docker, any machine that can run docker **should** be compatible with Kalavai. Here are instructions for [linux](https://docs.docker.com/engine/install/), [Windows](https://docs.docker.com/desktop/setup/install/windows-install/) and [MacOS](https://docs.docker.com/desktop/setup/install/mac-install/).

The kalavai client, which controls and access pools, can be installed on any machine that has python 3.6+.

**Support for Windows and MacOS workers is experimental**: kalavai workers run on docker containers that require access to the host network interfaces, thus systems that do not support containers natively (Windows and MacOS) may have difficulties finding each other.

Any system that runs python 3.6+ is able to run the `kalavai-client` and therefore connect and operate an LLM pool, [without sharing with the pool](getting_started.md#3-attach-more-clients). Your computer won't be adding its capacity to the pool, but it wil be able to deploy jobs and interact with models.


### Hardware compatibility:

- `amd64` or `x86_64` CPU architecture
- NVIDIA GPU
- AMD and Intel GPUs are currently not supported (yet!)


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


## Help testing AMD GPUs

If you are interested in testing AMD support within Kalavai and own an AMD GPU card, please [contact us](mailto:info@kalavai.net) or [create an issue](https://github.com/kalavai-net/kalavai-client/issues)!
