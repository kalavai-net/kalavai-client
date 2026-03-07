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




## Benchmark interconnectivity across GPUs

Docker (single node):

```bash
docker run --rm --gpus all \
  --shm-size=2g \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  nvcr.io/nvidia/pytorch:24.01-py3 \
  all_reduce_perf -b 8 -e 2G -f 2 -g 2
```
where -g is the number of GPUs within a node to use

Results

```bash
# nThread 1 nGpus 2 minBytes 8 maxBytes 2147483648 step: 2(factor) warmup iters: 5 iters: 20 agg iters: 1 validation: 1 graph: 0
#
# Using devices
#  Rank  0 Group  0 Pid      1 on f7dce118f2b2 device  0 [0x1a] NVIDIA GeForce RTX 4090
#  Rank  1 Group  0 Pid      1 on f7dce118f2b2 device  1 [0x1b] NVIDIA GeForce RTX 4090
#
#                                                              out-of-place                       in-place          
#       size         count      type   redop    root     time   algbw   busbw #wrong     time   algbw   busbw #wrong
#        (B)    (elements)                               (us)  (GB/s)  (GB/s)            (us)  (GB/s)  (GB/s)       
           8             2     float     sum      -1     8.97    0.00    0.00      0     8.83    0.00    0.00      0
          16             4     float     sum      -1     9.48    0.00    0.00      0     9.10    0.00    0.00      0
          32             8     float     sum      -1    10.28    0.00    0.00      0     9.34    0.00    0.00      0
          64            16     float     sum      -1     9.06    0.01    0.01      0     9.12    0.01    0.01      0
         128            32     float     sum      -1     9.85    0.01    0.01      0     8.98    0.01    0.01      0
         256            64     float     sum      -1     9.72    0.03    0.03      0     9.47    0.03    0.03      0
         512           128     float     sum      -1    10.57    0.05    0.05      0     9.22    0.06    0.06      0
        1024           256     float     sum      -1    10.37    0.10    0.10      0     9.60    0.11    0.11      0
        2048           512     float     sum      -1    10.94    0.19    0.19      0    10.16    0.20    0.20      0
        4096          1024     float     sum      -1    12.01    0.34    0.34      0    11.59    0.35    0.35      0
        8192          2048     float     sum      -1    16.82    0.49    0.49      0    16.27    0.50    0.50      0
       16384          4096     float     sum      -1    23.67    0.69    0.69      0    23.19    0.71    0.71      0
       32768          8192     float     sum      -1    40.18    0.82    0.82      0    40.19    0.82    0.82      0
       65536         16384     float     sum      -1    60.23    1.09    1.09      0    59.09    1.11    1.11      0
      131072         32768     float     sum      -1    97.90    1.34    1.34      0    98.15    1.34    1.34      0
      262144         65536     float     sum      -1    163.4    1.60    1.60      0    163.6    1.60    1.60      0
      524288        131072     float     sum      -1    280.1    1.87    1.87      0    280.6    1.87    1.87      0
     1048576        262144     float     sum      -1    538.5    1.95    1.95      0    537.4    1.95    1.95      0
     2097152        524288     float     sum      -1   1025.7    2.04    2.04      0   1021.7    2.05    2.05      0
     4194304       1048576     float     sum      -1   2022.1    2.07    2.07      0   2027.9    2.07    2.07      0
     8388608       2097152     float     sum      -1   4077.0    2.06    2.06      0   4077.4    2.06    2.06      0
    16777216       4194304     float     sum      -1   8137.9    2.06    2.06      0   7843.3    2.14    2.14      0
    33554432       8388608     float     sum      -1    15190    2.21    2.21      0    15738    2.13    2.13      0
    67108864      16777216     float     sum      -1    30690    2.19    2.19      0    30234    2.22    2.22      0
   134217728      33554432     float     sum      -1    60326    2.22    2.22      0    60565    2.22    2.22      0
   268435456      67108864     float     sum      -1   120583    2.23    2.23      0   120471    2.23    2.23      0
   536870912     134217728     float     sum      -1   241172    2.23    2.23      0   240466    2.23    2.23      0
  1073741824     268435456     float     sum      -1   478533    2.24    2.24      0   479466    2.24    2.24      0
  2147483648     536870912     float     sum      -1   957746    2.24    2.24      0   962086    2.23    2.23      0
# Out of bounds values : 0 OK
# Avg bus bandwidth    : 1.18707 
```

Results (4 GPUs):

```bash
# nThread 1 nGpus 4 minBytes 8 maxBytes 2147483648 step: 2(factor) warmup iters: 5 iters: 20 agg iters: 1 validation: 1 graph: 0
#
# Using devices
#  Rank  0 Group  0 Pid      1 on bd4e8bef7fdf device  0 [0x1a] NVIDIA GeForce RTX 4090
#  Rank  1 Group  0 Pid      1 on bd4e8bef7fdf device  1 [0x1b] NVIDIA GeForce RTX 4090
#  Rank  2 Group  0 Pid      1 on bd4e8bef7fdf device  2 [0x3d] NVIDIA GeForce RTX 4090
#  Rank  3 Group  0 Pid      1 on bd4e8bef7fdf device  3 [0x3e] NVIDIA GeForce RTX 4090
#
#                                                              out-of-place                       in-place          
#       size         count      type   redop    root     time   algbw   busbw #wrong     time   algbw   busbw #wrong
#        (B)    (elements)                               (us)  (GB/s)  (GB/s)            (us)  (GB/s)  (GB/s)       
           8             2     float     sum      -1    18.90    0.00    0.00      0    19.54    0.00    0.00      0
          16             4     float     sum      -1    20.58    0.00    0.00      0    19.01    0.00    0.00      0
          32             8     float     sum      -1    20.72    0.00    0.00      0    18.50    0.00    0.00      0
          64            16     float     sum      -1    20.29    0.00    0.00      0    19.38    0.00    0.00      0
         128            32     float     sum      -1    20.51    0.01    0.01      0    18.51    0.01    0.01      0
         256            64     float     sum      -1    20.79    0.01    0.02      0    20.24    0.01    0.02      0
         512           128     float     sum      -1    19.86    0.03    0.04      0    20.47    0.03    0.04      0
        1024           256     float     sum      -1    20.95    0.05    0.07      0    19.34    0.05    0.08      0
        2048           512     float     sum      -1    20.43    0.10    0.15      0    20.22    0.10    0.15      0
        4096          1024     float     sum      -1    20.61    0.20    0.30      0    20.81    0.20    0.30      0
        8192          2048     float     sum      -1    23.52    0.35    0.52      0    22.92    0.36    0.54      0
       16384          4096     float     sum      -1    31.99    0.51    0.77      0    31.39    0.52    0.78      0
       32768          8192     float     sum      -1    44.12    0.74    1.11      0    43.89    0.75    1.12      0
       65536         16384     float     sum      -1    81.19    0.81    1.21      0    79.88    0.82    1.23      0
      131072         32768     float     sum      -1    125.5    1.04    1.57      0    124.1    1.06    1.58      0
      262144         65536     float     sum      -1    211.5    1.24    1.86      0    210.9    1.24    1.86      0
      524288        131072     float     sum      -1    347.4    1.51    2.26      0    347.6    1.51    2.26      0
     1048576        262144     float     sum      -1    642.4    1.63    2.45      0    641.2    1.64    2.45      0
     2097152        524288     float     sum      -1   1251.1    1.68    2.51      0   1250.2    1.68    2.52      0
     4194304       1048576     float     sum      -1   2474.5    1.70    2.54      0   2459.8    1.71    2.56      0
     8388608       2097152     float     sum      -1   4883.4    1.72    2.58      0   4891.7    1.71    2.57      0
    16777216       4194304     float     sum      -1   9782.3    1.72    2.57      0   9750.6    1.72    2.58      0
    33554432       8388608     float     sum      -1    19546    1.72    2.58      0    19605    1.71    2.57      0
    67108864      16777216     float     sum      -1    39174    1.71    2.57      0    39148    1.71    2.57      0
   134217728      33554432     float     sum      -1    78219    1.72    2.57      0    78281    1.71    2.57      0
   268435456      67108864     float     sum      -1   156396    1.72    2.57      0   156386    1.72    2.57      0
   536870912     134217728     float     sum      -1   312692    1.72    2.58      0   312521    1.72    2.58      0
  1073741824     268435456     float     sum      -1   624356    1.72    2.58      0   624605    1.72    2.58      0
  2147483648     536870912     float     sum      -1  1246110    1.72    2.59      0  1246603    1.72    2.58      0
# Out of bounds values : 0 OK
# Avg bus bandwidth    : 1.40135 
#
```


Docker (multi node):

```bash
docker run --gpus all --net=host --shm-size=1g \
  nvcr.io/nvidia/pytorch:24.01-py3 \
  mpirun -np 2 -H <node1_ip>:1,<node2_ip>:1 \
  /usr/local/bin/all_reduce_perf -b 8 -e 1G -f 2 -g 1
```

Kubernetes (single node):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nccl-benchmark
spec:
  nodeSelector:
    kubernetes.io/hostname: ezc-kalavai-14h-f782feb9
  containers:
  - name: nccl-test
    image: nvcr.io/nvidia/pytorch:24.01-py3
    # Launch all_reduce test across 2 GPUs
    command: ["all_reduce_perf"]
    args: ["-b", "8", "-e", "2G", "-f", "2", "-g", "2"]
    resources:
      limits:
        nvidia.com/gpu: 2 # Match this to your -g arg above
    volumeMounts:
    - name: dshm
      mountPath: /dev/shm
  volumes:
  - name: dshm
    emptyDir:
      medium: Memory
      sizeLimit: 2Gi
  restartPolicy: Never
```

Results (2 GPUs)
```bash
# nThread 1 nGpus 2 minBytes 8 maxBytes 2147483648 step: 2(factor) warmup iters: 5 iters: 20 agg iters: 1 validation: 1 graph: 0
#
# Using devices
#  Rank  0 Group  0 Pid      1 on nccl-benchmark device  0 [0x1a] NVIDIA GeForce RTX 4090
#  Rank  1 Group  0 Pid      1 on nccl-benchmark device  1 [0xb2] NVIDIA GeForce RTX 4090
#
#                                                              out-of-place                       in-place          
#       size         count      type   redop    root     time   algbw   busbw #wrong     time   algbw   busbw #wrong
#        (B)    (elements)                               (us)  (GB/s)  (GB/s)            (us)  (GB/s)  (GB/s)       
           8             2     float     sum      -1    10.98    0.00    0.00      0    10.36    0.00    0.00      0
          16             4     float     sum      -1    12.26    0.00    0.00      0    11.89    0.00    0.00      0
          32             8     float     sum      -1    11.44    0.00    0.00      0    11.19    0.00    0.00      0
          64            16     float     sum      -1    12.11    0.01    0.01      0    11.16    0.01    0.01      0
         128            32     float     sum      -1    12.34    0.01    0.01      0    11.33    0.01    0.01      0
         256            64     float     sum      -1    11.44    0.02    0.02      0    11.40    0.02    0.02      0
         512           128     float     sum      -1    12.85    0.04    0.04      0    11.72    0.04    0.04      0
        1024           256     float     sum      -1    12.24    0.08    0.08      0    11.50    0.09    0.09      0
        2048           512     float     sum      -1    12.21    0.17    0.17      0    11.59    0.18    0.18      0
        4096          1024     float     sum      -1    12.53    0.33    0.33      0    11.80    0.35    0.35      0
        8192          2048     float     sum      -1    13.49    0.61    0.61      0    13.47    0.61    0.61      0
       16384          4096     float     sum      -1    17.61    0.93    0.93      0    16.91    0.97    0.97      0
       32768          8192     float     sum      -1    25.42    1.29    1.29      0    24.94    1.31    1.31      0
       65536         16384     float     sum      -1    44.14    1.48    1.48      0    43.48    1.51    1.51      0
      131072         32768     float     sum      -1    64.38    2.04    2.04      0    64.38    2.04    2.04      0
      262144         65536     float     sum      -1    97.63    2.69    2.69      0    97.21    2.70    2.70      0
      524288        131072     float     sum      -1    161.8    3.24    3.24      0    162.3    3.23    3.23      0
     1048576        262144     float     sum      -1    300.6    3.49    3.49      0    296.7    3.53    3.53      0
     2097152        524288     float     sum      -1    603.9    3.47    3.47      0    604.4    3.47    3.47      0
     4194304       1048576     float     sum      -1   1182.0    3.55    3.55      0   1178.8    3.56    3.56      0
     8388608       2097152     float     sum      -1   2343.3    3.58    3.58      0   2307.9    3.63    3.63      0
    16777216       4194304     float     sum      -1   4559.1    3.68    3.68      0   4563.6    3.68    3.68      0
    33554432       8388608     float     sum      -1   9106.9    3.68    3.68      0   9100.1    3.69    3.69      0
    67108864      16777216     float     sum      -1    18091    3.71    3.71      0    18078    3.71    3.71      0
   134217728      33554432     float     sum      -1    36154    3.71    3.71      0    36073    3.72    3.72      0
   268435456      67108864     float     sum      -1    71901    3.73    3.73      0    71773    3.74    3.74      0
   536870912     134217728     float     sum      -1   143148    3.75    3.75      0   142502    3.77    3.77      0
  1073741824     268435456     float     sum      -1   281237    3.82    3.82      0   281716    3.81    3.81      0
  2147483648     536870912     float     sum      -1   557166    3.85    3.85      0   554637    3.87    3.87      0
# Out of bounds values : 0 OK
# Avg bus bandwidth    : 1.96915 
#
```

Results (4 GPUs)


```bash
# nThread 1 nGpus 4 minBytes 8 maxBytes 2147483648 step: 2(factor) warmup iters: 5 iters: 20 agg iters: 1 validation: 1 graph: 0
#
# Using devices
#  Rank  0 Group  0 Pid      1 on nccl-benchmark device  0 [0x1a] NVIDIA GeForce RTX 4090
#  Rank  1 Group  0 Pid      1 on nccl-benchmark device  1 [0x1b] NVIDIA GeForce RTX 4090
#  Rank  2 Group  0 Pid      1 on nccl-benchmark device  2 [0x3d] NVIDIA GeForce RTX 4090
#  Rank  3 Group  0 Pid      1 on nccl-benchmark device  3 [0x3e] NVIDIA GeForce RTX 4090
#
#                                                              out-of-place                       in-place          
#       size         count      type   redop    root     time   algbw   busbw #wrong     time   algbw   busbw #wrong
#        (B)    (elements)                               (us)  (GB/s)  (GB/s)            (us)  (GB/s)  (GB/s)       
           8             2     float     sum      -1    20.46    0.00    0.00      0    18.75    0.00    0.00      0
          16             4     float     sum      -1    21.06    0.00    0.00      0    19.71    0.00    0.00      0
          32             8     float     sum      -1    21.20    0.00    0.00      0    19.42    0.00    0.00      0
          64            16     float     sum      -1    19.59    0.00    0.00      0    19.41    0.00    0.00      0
         128            32     float     sum      -1    21.28    0.01    0.01      0    18.45    0.01    0.01      0
         256            64     float     sum      -1    20.93    0.01    0.02      0    19.40    0.01    0.02      0
         512           128     float     sum      -1    20.97    0.02    0.04      0    18.59    0.03    0.04      0
        1024           256     float     sum      -1    20.63    0.05    0.07      0    19.85    0.05    0.08      0
        2048           512     float     sum      -1    20.60    0.10    0.15      0    18.66    0.11    0.16      0
        4096          1024     float     sum      -1    21.98    0.19    0.28      0    20.00    0.20    0.31      0
        8192          2048     float     sum      -1    22.93    0.36    0.54      0    23.36    0.35    0.53      0
       16384          4096     float     sum      -1    32.21    0.51    0.76      0    30.71    0.53    0.80      0
       32768          8192     float     sum      -1    44.70    0.73    1.10      0    43.91    0.75    1.12      0
       65536         16384     float     sum      -1    81.53    0.80    1.21      0    80.08    0.82    1.23      0
      131072         32768     float     sum      -1    124.3    1.05    1.58      0    122.0    1.07    1.61      0
      262144         65536     float     sum      -1    210.1    1.25    1.87      0    210.6    1.24    1.87      0
      524288        131072     float     sum      -1    347.1    1.51    2.27      0    346.7    1.51    2.27      0
     1048576        262144     float     sum      -1    640.0    1.64    2.46      0    641.9    1.63    2.45      0
     2097152        524288     float     sum      -1   1260.5    1.66    2.50      0   1251.0    1.68    2.51      0
     4194304       1048576     float     sum      -1   2468.3    1.70    2.55      0   2467.5    1.70    2.55      0
     8388608       2097152     float     sum      -1   4907.7    1.71    2.56      0   4916.2    1.71    2.56      0
    16777216       4194304     float     sum      -1   9770.1    1.72    2.58      0   9779.5    1.72    2.57      0
    33554432       8388608     float     sum      -1    19592    1.71    2.57      0    19586    1.71    2.57      0
    67108864      16777216     float     sum      -1    39102    1.72    2.57      0    39125    1.72    2.57      0
   134217728      33554432     float     sum      -1    78286    1.71    2.57      0    78260    1.72    2.57      0
   268435456      67108864     float     sum      -1   156229    1.72    2.58      0   156226    1.72    2.58      0
   536870912     134217728     float     sum      -1   312377    1.72    2.58      0   311761    1.72    2.58      0
  1073741824     268435456     float     sum      -1   622331    1.73    2.59      0   622115    1.73    2.59      0
  2147483648     536870912     float     sum      -1  1242243    1.73    2.59      0  1242476    1.73    2.59      0
# Out of bounds values : 0 OK
# Avg bus bandwidth    : 1.40254 
#
```

Kubernetes (multi-node):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nccl-service
spec:
  clusterIP: None
  selector:
    app: nccl-test
  ports:
  - port: 12345
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nccl-test
spec:
  serviceName: "nccl-service"
  replicas: 2
  selector:
    matchLabels:
      app: nccl-test
  template:
    metadata:
      labels:
        app: nccl-test
    spec:
      nodeSelector:
        kalavai: "yes"
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: ["nccl-test"]
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: nccl-container
        image: nvcr.io/nvidia/pytorch:24.01-py3
        resources:
          limits:
            nvidia.com/gpu: 1
        volumeMounts:
        - name: dshm
          mountPath: /dev/shm
        env:
        - name: NCCL_DEBUG
          value: "INFO"
        - name: NCCL_SOCKET_IFNAME
          value: "eth0"
        # The Automated Execution Logic
        command: ["/bin/bash", "-c"]
        args:
        - |
          # 1. Determine if I am the "Launcher" (Rank 0) or "Worker" (Rank 1)
          if [[ $(hostname) == "nccl-test-0" ]]; then
            echo "I am Rank 0. Waiting for nccl-test-1 to be online..."
            
            # 2. Wait for the peer pod to become reachable
            until getent hosts nccl-test-1.nccl-service; do
              sleep 2
            done
            
            echo "Peer found. Launching NCCL benchmark..."
            
            # 3. Run the test across both pods
            mpirun --allow-run-as-root \
              -np 2 \
              -H nccl-test-0.nccl-service:1,nccl-test-1.nccl-service:1 \
              --bind-to none --map-by slot \
              /usr/local/bin/all_reduce_perf -b 8 -e 1G -f 2 -g 1
            
            echo "Test Complete. Keeping pod alive for logs..."
            sleep infinity
          else
            echo "I am Rank 1. Standing by for Rank 0..."
            sleep infinity
          fi
      volumes:
      - name: dshm
        emptyDir:
          medium: Memory
          sizeLimit: 2Gi
```


OR


```yaml
apiVersion: v1
kind: Service
metadata:
  name: nccl-service
spec:
  clusterIP: None # Headless service for direct pod-to-pod comms
  selector:
    app: nccl-test
  ports:
  - port: 12345 # Random port for NCCL handshake
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nccl-test
spec:
  serviceName: "nccl-service"
  replicas: 2
  selector:
    matchLabels:
      app: nccl-test
  template:
    metadata:
      labels:
        app: nccl-test
    spec:
      nodeSelector:
        kalavai: "yes"
      # Anti-affinity ensures they land on DIFFERENT nodes
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: ["nccl-test"]
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: nccl-container
        image: nvcr.io/nvidia/pytorch:24.01-py3
        env:
        - name: NCCL_DEBUG
          value: "INFO"
        # IMPORTANT: Tell NCCL to use the VPN interface (usually eth0 or tun0)
        - name: NCCL_SOCKET_IFNAME
          value: "netmaker" 
        resources:
          limits:
            nvidia.com/gpu: 1
        volumeMounts:
        - name: dshm
          mountPath: /dev/shm
        # Keep the pod alive so we can exec into it
        command: ["/bin/bash", "-c", "sleep infinity"]
      volumes:
      - name: dshm
        emptyDir:
          medium: Memory
          sizeLimit: 2Gi
```

Then enter node 1:


