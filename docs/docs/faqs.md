---
tags:
  - FAQs
---
# FAQs

## General

### What are clusters?

In Kalavai parlor, a cluster refers to a group of resources. We go beyond machine procurement and include everything a team needs to work on AI; from the hardware devices (GPUs, CPUs and memory) to the setup of a distributed environment and the tech stack needed to make it useful.

Kalavai aims to manage it all (procurement of additional cloud resources, installing and configuring open source and industry standard frameworks, configuration management, facilitate distributed computing) so teams can focus on AI innovation.


### Isn’t the performance of distributed training much slower?

Distributed computing is not an option: due to the skyrocketing demand in computation from AI models, we are going to need to use multiple devices to do training and inference. 

NVIDIA cannot get devices larger fast enough, and cloud providers are busy counting the money they are going to make from all that computing to care.

Kalavai has considerable tailwinds that will work to minimise the impact of distributed computing in the future: 
- Consumer-grade GPU performance per dollar is improving at a faster rate than cloud GPUs
- By 2030: Internet broadband speed will reach Gbit/s and 6G will reduce latency < 1 microsecond


## Host nodes

##### What are the minimum specs for sharing?

##### Is my device safe?

##### Can I use my device whilst sharing?

##### Can I limit what I share with Kalavai?

##### Why does it require sudo privileges?


## Developers

### There are plenty of MLOps platforms out there, why would organisations turn to you instead?

MLOps solutions out there are great, and they continue to develop. But they all need hardware to run on; whether it is on premise servers, public cloud resources or managed services. 

We think of MLOps platforms as complementors, that’s why we are building a marketplace for third parties to bring their solutions to our users. Since we manage the computing layer, we abstract away the complexity of integration for them, so they can also bring their tools without having to build multiple integrations.



## Enterprises

### You are leveraging the organisation's existing hardware, but this is unlikely to meet AI demands. Are we not back to square one since they need to anyways go to the cloud?

Our goal is not to narrow companies' choices but to manage the complexity of hybrid clouds. Organisations can bring hardware from anywhere (their own premises, their company devices, all the way to multi cloud on-demand resources) and Kalavai manages them equally. Developers then see a pool of resources that they treat the same.


### Organisations with on premise servers already have systems to use them. Why would they trust you to manage that for all their needs?

Kalavai works as an integration system, it does not force organisations to switch every workflow they have over to benefit from it. They can install the kalavai client in their existing on premise servers, which will automatically then connect them to the cluster and make them able to run workflows. The kalavai client is designed to co-exist with any application and can be limited to use only a portion of resources, so organisations can easily continue to use their on premise deployments.


### I’ve heard of a bunch of service providers for rent-a-GPU on demand. Isn’t the market saturated already?

Kalavai does not have any hardware to lease. We believe there are enough providers out there to cover that. Where there’s a gap is in managing the complexity of use cases that require distributed computing. When workflows require more than one computing device to run, organisations need to manage the orchestration, maintenance and coordination of devices.

We have designed Kalavai to integrate nicely with almost any computing resource out there, from public cloud, serverless GPU providers and on premise devices.



[Got another question?](mailto:info@kalavai.net?subject=Question){ .md-button .md-button--primary}
