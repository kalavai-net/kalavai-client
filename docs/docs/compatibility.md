---
tags:
  - requirements
  - compatibility
---

# Compatibility matrix

If your system is not currently supported, [open an issue](https://github.com/kalavai-net/kalavai-client/issues) and request it. We are expanding this list constantly.


### OS compatibility

Currently compatible and tested OS:
- Ubuntu (22.04, 24.04)
- Pop! OS 22.04
- Windows 10+ (using WSL2)

Currently compatible (untested. [Interested in testing them?](#help-testing-new-systems)):
- Debian-based linux
- Fedora
- RedHat
- Any distro capable of installing `.deb` and `.rpm` packages.

Currently not compatible:
- MacOS


## Help testing new systems

If you want to help testing Kalavai in new Windows / Linux based systems (thank you!), follow the next steps:

1. For linux distros, use the [linux install instructions](getting_started.md#linux) to get kalavai in your system. For windows systems, use the [windows install instructions](getting_started.md#windows)

2. Save the entire install logs (printed out in the console) to a file (install.log)

3. If the installation went through, run kalavai commands to test the output:
```bash
kalavai pool status > status.log
kalavai pool start test > test_pool.log
kalavai pool resources > resources.log
```

4. Create an [issue on our repo](https://github.com/kalavai-net/kalavai-client/issues) and share the results. Include the four log files (status.log, test_pool.log, resources.log and install.log) as well as a description of the system you are testing.

5. If the system ends up being supported, you'll be invited to create a PR to add support to the compatibility matrix.
