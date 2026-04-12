---
tags:
  - serverless gpus
  - gpu capacity
  - gpu fleet
  - architecture
---

## Architecture of a Serverless GPU Fleet: Technical Overview

Kalavai is a distributed orchestration layer designed to decouple compute-intensive AI workloads from fixed hardware constraints. Unlike traditional static provisioning (e.g., persistent VM instances), Kalavai implements a **disaggregated resource model**. It treats a heterogeneous GPU fleet as a single, virtualized pool of FLOPs and VRAM, managed through a container-native scheduler.

### Why the Serverless Approach?

For a technical lead, the "Serverless" GPU approach solves the **Hardware Lifecycle Problem**. Instead of managing a fleet of "pets" (specific servers with specific drivers), you manage a _utility_. This architecture ensures that compute is treated as a transient, fungible commodity, allowing the engineering team to optimize for **throughput per dollar** rather than **uptime per server**.


### The Virtualization & Abstraction Layer

The core of the serverless approach lies in the **Virtual Control Plane**. Instead of mapping a job to a specific `node_id`, Kalavai utilizes a declarative intent-based model.

* **Resource Discovery:** An agent-based mesh identifies available CUDA cores, interconnect bandwidth (NVLink/PCIe), and VRAM across the fleet.
* **Dynamic Binding:** Workloads are containerized and bound to GPU resources only at runtime. This allows for **preemption-aware scheduling**, where low-priority batch jobs (training) can be evicted for high-priority latency-sensitive tasks (inference).
* **Namespace Isolation:** Utilizing cgroups and NVIDIA Container Toolkit (libnvidia-container) to ensure strict multi-tenant isolation at the driver level.


### Just-in-Time (JIT) Infrastructure

The _serverless_ aspect is achieved through a **Cold-Start Optimized Scheduler**.

* **Template Logic:** Templates are not just UI shortcuts; they are **Custom Resource Definitions (CRDs)**. They define capacity requirements (e.g., `min_vram: 24GB`) and the runtime environment (e.g. base image + Weights).
* **Provisioning Flow:** When an API call is received, the orchestrator evaluates the current fleet state and assigns resources dynamically to maximise fleet utilisation (fractional GPUs, heterogeneous assignments) that match the template requirements.
* **Auto-reprovisioning**: if not enough resources are available, the orchestrator can automatically provision new nodes to meet the demand from external cloud, on premises or Kalavai-managed GPUs.


### Elasticity & Scaling Mechanics

The platform achieves autoscaling by monitoring **GPU-specific telemetry**.

* **Scale-to-Zero:** Using a request-buffering proxy, Kalavai can hold incoming inference requests in a queue while spinning up a GPU consumer, effectively reducing idle costs to $0$.
* **Horizontal Autoscaling:** Scales based on `GPU Utilization`, `memory` or `concurrent requests`, all customized to meet use case SLAs.
* **Data Locality Optimization:** The scheduler attempts to place workloads on nodes with pre-cached model weights or proximity to the data lake to minimize ingress/egress overhead.


### Technical Benefits for Engineers

| Feature | Technical Implementation | Engineering Impact |
| --- | --- | --- |
| **Unified Interface** | Abstracted CLI/API over K8s/Slurm/Bare-metal | Reduced DevOps overhead; no more manual SSH/Driver management. |
| **Interconnect Aware** | Topology-aware placement for multi-node jobs | Optimizes `All-Reduce` operations in distributed training. |
| **Ephemeral Runtimes** | Immutable, versioned container environments | Eliminates "it works on my machine" and driver version conflicts. |
| **Cost Engineering** | Spot instance integration with automated checkpointing | Enables 70-90% cost reduction via high-risk/low-cost hardware. |


## The Templating & Extensibility Framework

Kalavai utilizes a [**Declarative Template Engine**](https://github.com/kalavai-net/kalavai-templates) that standardizes how AI workloads interact with a heterogeneous GPU fleet. By defining workloads as templates, the platform removes the need for manual node configuration, ensuring that environments are immutable and reproducible.


### Built-in "Off-the-Shelf" Stacks

For immediate deployment, Kalavai provides optimized, pre-configured runtimes for the industry's most common architectural patterns:

| Workload Category | Supported Engines / Frameworks | Optimization Focus |
| --- | --- | --- |
| **LLM Inference** | vLLM, SGLang, llama.cpp | Throughput, KV cache management, and PagedAttention. |
| **Image Generation** | Stable Diffusion (Diffusers), ComfyUI | Cold-start latency and VRAM footprint optimization. |
| **Audio & Speech** | Speaches (Whisper/TTS) | Real-time factor (RTF) and concurrency handling. |
| **Fine-Tuning** | LoRA / QLoRA (PEFT) | Efficient gradient checkpointing and memory-efficient backprop. |
| **Multi-GPU Training** | Ray Clusters, PyTorch DDP | Inter-node communication (NCCL) and topology-aware placement. |


### Extensibility via Custom Templates

For specialized pipelines, Kalavai provides a **Template Specification Language** (based on YAML/JSON) that allows engineering teams to define custom execution contexts.

* **Custom Runtimes:** Define your own OCI-compliant container images with specific CUDA/ROCm driver requirements.
* **Parameterized Logic:** Expose variables (e.g., `MODEL_ID`, `BATCH_SIZE`, `MAX_VRAM`) to the end-user, while the template handles the underlying orchestration.
* **Plug-and-Play Integration:** Easily integrate proprietary model architectures or specialized preprocessing scripts into the Kalavai scheduler.
* **Infrastructure-as-Code (IaC):** Treat your GPU workloads like software. Templates are version-controlled, allowing for `diff`-based infrastructure updates and easy rollbacks.


### The Technical "Why": Decoupling Logic from Hardware

In a traditional setup, you build an environment *on* a specific server. In Kalavai’s serverless model:

1. **The Template** defines the requirements (e.g., *“I need 40GB VRAM and an RDMA-capable interconnect”*).
2. **The Orchestrator** scans the global fleet for a match.
3. **The Runtime** is injected into the matching node via the Kalavai agent.

This decoupling allows you to swap out hardware—moving from an on-prem RTX 4090 cluster to a cloud H100 fleet—without changing a single line of your workload logic.
