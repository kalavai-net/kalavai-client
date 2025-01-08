---
tags:
  - job
  - resources
  - estimate resources
---

> Work in progress.

# Choosing pool resources for your jobs

For this example we don't need to tweak resource parameters, but for other models you may need to up the number of workers, desired RAM, etc. More information in the internal documentation of the engine's template ([vLLM](https://github.com/kalavai-net/kalavai-client/tree/main/templates/vllm), [llama.cpp](https://github.com/kalavai-net/kalavai-client/tree/main/templates/llamacpp)). If you want help on how much a model may require, you can use our internal estimation tool:

kalavai job estimate <number of billion of parameters> --precision <precision>

For example, to deploy a 1B model at 16 floating point precision:

```bash
$ kalavai job estimate 1 --precision 16

There are 3 GPUs available (24.576GBs) 
A 1B model requires ~1.67GB vRAM at 16bits precision
Looking at current capacity, use 1 GPU workers for a total 4.10 GB vRAM
```
