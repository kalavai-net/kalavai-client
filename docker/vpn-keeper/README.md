# Utility to keep VPN hosts alive

High values on MTU nodes can lead to loss of connectivity (ping) between server and nodes in Netmaker VPN. We have noticed that refreshing the host keys solves the issue.

This utility keeps nodes that are connected alive by periodically refreshing when not ping is detected.

## How to set up

On a self hosted netmaker network.

1. Install netmaker

2. Configure the domain and create a network (which will let you generate a subnet)

3. Get API KEY for it

```bash
# find MASTER_KEY
cat netmaker.env
```

4. Run keeper:

```bash
docker run -d \
    --net host \
    -e API_KEY=<your master key> \
    -e API_URL=<https://api.netmaker.YOUR.DOMAIN> \
    -e SUBNET=<your subnet> \
    bundenth/vpn-keeper:latest
```
