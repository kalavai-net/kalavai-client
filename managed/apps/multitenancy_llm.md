---
tags:
  - multi-tenancy
  - llm
  - api gateway
  - inference
---

| WIP |
|-----|
| This page is currently under development |

Features:
- Manage multiple AI deployments in one place
- Support for LLMs, diffusion pipelines, audio models and more
- Auto deployment on Kalavai infrastructure (no devops required)
- Automatically scale up and down based on demand
- Access control via API keys
- Usage tracking and billing
- Extensive library of pre-configured models and templates

## Getting started

Closed access by invitation. Interested? Contact...

Steps to get started:

1. Configure HF_TOKEN value (readonly recommended)
2. Deploy a model via Deploy Model
3. Generate an API key in LLM Gateway
4. List model availability in Deployments
5. Use the API key to access the deployed model


## Advanced

### Monitoring and access control

Via LiteLLM, you can monitor and control the access to each model, and create custom rules for each tenant. Visit the Management dashboard under LLM Gateway. Credentials listed in there.

### Cost control

Setup pricing for models based on token usage via LiteLLM.

### Adding custom models

(coming soon) You can add custom models to the deployment via Configuration.