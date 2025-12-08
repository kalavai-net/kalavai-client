# Useful scripts

## Worker installers

Individual scripts to setup workers on various platforms. Workers are docker compose recipes that run kalavai-runner and vpn containers to connect to a pool. They do not include the kalavai-client. Workers are useful in organisations where you want to increase the computational workforce in machines where the client is not required (cloud instances, worker-only nodes).


## QCOW images

Kalavai client as a QCOW image

Docker to QCOW: https://github.com/linka-cloud/d2vm

docker pull linkacloud/d2vm:latest
alias d2vm="docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock --privileged -v \$PWD:/d2vm -w /d2vm linkacloud/d2vm:latest"

For images:

d2vm convert <repo>/<image_id>

For dockerfiles:

d2vm build . -f Dockerfile --size 500G --output kalavai.qcow2 --password <root_password>


### Example

```bash
d2vm build . -f qcow2.Dockerfile --size 500G --output kalavai_nvidia.qcow2 --password password --build-arg KALAVAI_VERSION=0.7.23 --build-arg KALAVAI_NODE_TAGS="testtag=qcow2" --build-arg KALAVAI_TOKEN=eyJjbHVzdGVyX2lwIjogIjE5Mi4xNjguNjguNjciLCAiY2x1c3Rlcl9uYW1lIjogImthbGF2YWlfY2x1c3RlciIsICJjbHVzdGVyX3Rva2VuIjogIksxMGU4ZmFjODBiYzVjOWNlODkzOTFlODliNTE3MTBmNjAxNzhjM2JmZDdiOWZjMWJlNzViODIwNTI3OGRmNDk3MjU6OnNlcnZlcjpjM2EwMDZkOGJjZjg4MDM0YjE2ZmYzY2M0Y2I1ZjY0YVxuIiwgIndhdGNoZXJfYWRtaW5fa2V5IjogIjExMzRkMDM3LTAzZDUtNGUyNy1iN2VhLWM3NzE4MTY2ZjRkMiIsICJ3YXRjaGVyX3NlcnZpY2UiOiAiMTkyLjE2OC42OC42NzozMDAwMSIsICJwdWJsaWNfbG9jYXRpb24iOiBudWxsfQ==
```


### Test locally

Use QEMU. Install dependencies:

sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager
sudo usermod -aG kvm $USER
sudo usermod -aG libvirt $USER

From GUI, run virt-manager:

sudo virt-manager

From CLI:

qemu-system-x86_64 \
    -enable-kvm \
    -m 4096 \
    -cpu host \
    -vga std \
    -hda kalavai_nvidia.qcow2 \
    -net nic,model=virtio -net user \
    -snapshot

## Using https://github.com/openstack/diskimage-builder

