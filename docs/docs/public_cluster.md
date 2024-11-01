---
tags:
  - crowdsource
  - public cluster
---

# Public clusters: crowdsource community resources

Our public platform expands local clusters in two key aspects:
- Worker nodes **no longer have to be in the same local network**
- Users can **tap into community resources**: inspire others in the community to join their projects with their resources

To get started, you need is a [free account on our platform](https://platform.kalavai.net).


### A) Tap into community resources

Create a new cluster, using a public location provided by Kalavai:
```bash
# Authenticate with your kalavai account
kalavai login

# Get available public locations
kalavai location list

┏━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓  
┃ VPN ┃ location    ┃ subnet        ┃          
┡━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ 0   │ uk_london_1 │ 100.10.0.0/16 │
└─────┴─────────────┴───────────────┘

# Create and publish your cluster
kalavai cluster start <cluster-name> --location uk_london_1
```

If all goes well, your cluster will be created and published on the `Public Seeds` section of our [platform](https://platform.kalavai.net)

![Public seeds](/docs/docs/assets/images/public_seeds.png)

Note: to be able to publish clusters your account needs to have sufficient karma points. Earn karma by [sharing your resources](#b-share-resources-with-inspiring-community-projects) with others.


### B) Share resources with inspiring community projects

Have idle computing resources? Wish to be part of exciting public projects? Want to give back to the community? Earn social credit (both literally and metaphorically) by sharing your computer with others within the community.

All you need is a public joining key. Get them in our platform, on the list of published clusters. Press `Join` and follow the instructions

![alt text](/docs/docs/assets/images/join_public_cluster.png)
