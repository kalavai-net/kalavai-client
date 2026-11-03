# Pre-requisites

## Software

Both worker and server nodes require `gcc` compiler and `python3-dev`: 

```bash
sudo apt install gcc g++ python3-dev
```

If you want to use Longhorn distributed storage, you need to install and configure open-iscsi:

```bash
sudo apt install open-iscsi
sudo modprobe iscsi_tcp
sudo modprobe dm_mod
echo "iscsi_tcp" | sudo tee -a /etc/modules-load.d/longhorn.conf
echo "dm_mod" | sudo tee -a /etc/modules-load.d/longhorn.conf
```


## Ports

Once a machine is part of a pool, the following ports must be enabled and open to accept and process workloads:

**Seed nodes**:

- 2379-2380 TCP inbound/outbound
- 6443 TCP inbound
- 8472 UDP inbound/outbound
- 10250 TCP inbound/outbound
- 51820-51821 UDP inbound/outbound


**Worker nodes**:

- 6443 TCP outbound
- 8472 UDP inbound/outbound
- 10250 TCP inbound/outbound
- 51820-51821 UDP inbound/outbound
- 5121 TCP inbound/outbound