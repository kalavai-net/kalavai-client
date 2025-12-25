---
tags:
  - ray
---

> Work in progress

# Ray clusters for distributed computing

From Ray's documentation:

> Ray is an open-source unified framework for scaling AI and Python applications like machine learning.

Kalavai and Ray work perfectly together. Ray is a great framework to deal with distributed computation on top of an existing hardware pool. Kalavai acts as a unifying layer that brings that required hardware together for Ray to do its magic.

To get started, check out [our example](/examples/ray_cluster.md) to get a Ray cluster going. 

## Create a cluster

- Specs how to define specs: kalavai pool resources (cpu, memory and nvidia.com/gpu)


```bash
$ kalavai pool resources

┏━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓ 
┃           ┃ n_nodes ┃ cpu                ┃ memory      ┃ nvidia.com/gpu ┃ 
┡━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩ 
│ Available │ 2       │ 10.684999999999999 │ 16537780224 │ 1              │ 
├───────────┼─────────┼────────────────────┼─────────────┼────────────────┤ 
│ Total     │ 4       │ 42                 │ 70895030272 │ 3              │ 
└───────────┴─────────┴────────────────────┴─────────────┴────────────────┘ 
```

```yaml
spec:
  ...
  headGroupSpec:
    ...
    template:
      spec:
        ...
        containers:
        ...
          resources:
            limits:
              cpu: 2
              memory: 4Gi
            requests:
              cpu: 2
              memory: 4Gi
  workerGroupSpecs:
  ...
    template:
      spec:
        containers:
        ...
          resources:
            limits:
              nvidia.com/gpu: 1
              cpu: 2
              memory: 4Gi
            requests:
              nvidia.com/gpu: 1
              cpu: 2
              memory: 4Gi
```


Interact with Ray
- Interactive mode
- Endpoint
- RayJobs


## Advanced topics

Autoscaling

Node hardware requirements (limits vs requests)

