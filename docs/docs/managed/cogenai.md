---
tags:
  - LLM hosting
  - LLM inference
  - CoGenAI
---

# Model self-hosting made easier: CoGenAI

[CoGenAI](https://cogenai.kalavai.net) is the easiest way to deploy and use LLMs.

Production ready
Single endpoint for all models
Scalable and resilient
No config, just works
Supported models growing
Explain params + example


Model Hosting with CoGenAI
Overview

CoGenAI
 is Kalavai’s managed model hosting platform — designed for self-hosting open-source LLMs (like Llama, Mistral, Falcon, etc.) with zero infrastructure setup.

It lets you deploy models directly into Kalavai’s managed environment — production-ready from day one.

Why CoGenAI?

Fully managed: No infrastructure or DevOps required

Scalable: Auto-scale inference pods based on load

Affordable: Pay only for the compute you use

Secure: Isolated environments with private model endpoints

Getting Started

Sign in to CoGenAI

Visit https://cogenai.kalavai.net

Log in or create your Kalavai account

Select a Base Model
Choose from supported open models (e.g., Llama 3, Mistral, Falcon).

Deploy Your Model

kalavai model deploy --model llama3 --name my-llm --gpus 2


Access Your Endpoint
Once deployed, CoGenAI provides an inference API endpoint:

curl -X POST https://api.cogenai.kalavai.net/v1/my-llm \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"prompt": "Hello Kalavai!"}'


Monitor and Scale

View logs and metrics via CoGenAI Dashboard

Adjust compute resources with one command:

kalavai model scale my-llm --gpus 4
