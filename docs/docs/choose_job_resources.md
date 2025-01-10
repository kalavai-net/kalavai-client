---
tags:
  - job
  - resources
  - estimate resources
---

> Work in progress.

# Choosing pool resources for your jobs

Jobs describe the required resources for workers. All of these parameters have default values which are generally good for most cases, but more demanding LLMs will require extra resources. Here are the general resource parameters that are common to all jobs. For engine-specific information, check out the documentation for the job ([vLLM](https://github.com/kalavai-net/kalavai-client/tree/main/templates/vllm), [llama.cpp](https://github.com/kalavai-net/kalavai-client/tree/main/templates/llamacpp))

- working_memory 
- cpus (per worker)
- memory (per worker RAM)

If you want help on how much a model may require, you can use our internal estimation tool:

kalavai job estimate <number of billion of parameters> --precision <precision>

For example, to deploy a 1B model at 16 floating point precision:

```bash
$ kalavai job estimate 1 --precision 16

There are 3 GPUs available (24.576GBs) 
A 1B model requires ~1.67GB vRAM at 16bits precision
Looking at current capacity, use 1 GPU workers for a total 4.10 GB vRAM
```
