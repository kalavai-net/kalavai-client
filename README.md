# kalavai-client

Public repository for the kalavai-client installer.

## Requirements

The kalavai client app currently supports the following architectures:
- amd64
- x86_64

The following OS are supported:
- Linux (Debian, RedHat, Ubuntu, Fedora... basically anything that can run deb and rpm packages).

If your system is not currently supported, open an issue and request it. We are expanding this list constantly.


## Install

To install the kalavai client app that allows you to share your device and earn, use the following installer:

```bash
curl -sfL https://raw.githubusercontent.com/kalavai-net/kalavai-client/main/scripts/install_client.sh | bash -
```

## Use kalavai-client

Once it's installed, run the CLI app with:

```bash
kalavai --help

usage: kalavai [-h] command ...

positional arguments:
  command
    login     Login with your Kalavai user email and password. Get an account from https://platform.kalavai.net
    logout    Logout from your kalavai user account.
    start     Join Kalavai cluster and start/resume sharing resources.
    status    Check the current status of your device.
    stop      Stop sharing your device and clean up. DO THIS ONLY IF YOU WANT TO REMOVE KALAVAI-CLIENT from your device.
    pause     Pause sharing your device and make your device unavailable for kalavai scheduling.

options:
  -h, --help  show this help message and exit
```

To start sharing your device, make sure to create an account at http://platform.kalavai.net and then log in with the client:

```bash
kalavai login --useremail your@email.address --password your-password
```

Once authenticated, you are ready to share with:
```bash
kalavai start
```

This will start the sharing loop. Head over to your [online account](http://platform.kalavai.net) to see the status.


