# kalavai-client

Public repository for the kalavai-client installer.

## Connect to Kalavai

```bash
curl -sfL https://raw.githubusercontent.com/kalavai-net/kalavai-client/main/scripts/apt_connect.sh | bash -
```

## Go client

Wrapper example: https://github.com/kalavai-net/kalavai-server/blob/main/main.go

Commands imported from k3s: https://github.com/k3s-io/k3s/tree/master/pkg/cli

### Build

git clone --recurse-submodules https://github.com/kalavai-net/kalavai-client
go mod init main
go mod tidy


Run:

go run .

