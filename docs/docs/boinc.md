---
tags:
  - boinc
  - volunteer computing
---

# BOINC: Volunteer scientific computing

BOINC is an open source platform for volunteer computing, organised in scientific projects.

Kalavai makes it easy to share your computing resources with [Science United](https://scienceunited.org/), a coordinated model for scientific computing where volunteers share their machines with a multitude of projects.

What you get by sharing:

- Eternal kudos from the community!
- Kalavai credits that can be used in any of our public pools


## Requirements

- A free Kalavai account. Create one [here](https://platform.kalavai.net).
- A computer with the minimum requirements (see below)

Hardware requirements

- 4+ CPUs
- 4GB+ RAM
- (optional) 1+ NVIDIA GPU


## How to join

1. Create a [free account](https://platform.kalavai.net) with Kalavai.

2. Install the kalavai client following the instructions [here](https://kalavai-net.github.io/kalavai-client/getting_started/). Currently we support Linux distros and Windows.

3. Get the joining token. Visit our [platform](https://platform.kalavai.net) and go to `Community pools`. Then click `Join` on the `BOINC` Pool to reveal the joining details. Copy the command (including the token).

![Join BOINC](/docs/docs/assets/images/join.png)

4. Authenticate the computer you want to use as worker:
```bash
$ kalavai login

[10:33:16] Kalavai account details. If you don't have an account, create one at https://platform.kalavai.net                                                                 
User email: <your email>
Password: <your password>

[10:33:25] <email> logged in successfully
```

5. Join the pool with the following command:

```bash
$ kalavai pool join <token>

[16:28:14] Token format is correct
           Joining private network

[16:28:24] Scanning for valid IPs...
           Using 100.10.0.8 address for worker
           Connecting to BOINC @ 100.10.0.9 (this may take a few minutes)...
[16:29:41] Worskpace created
           You are connected to BOINC
```

**That's it, your machine is now contributing to scientific discovery!**


## Stop sharing

You can either pause sharing, or stop and leave the pool altogether (don't worry, you can rejoin using the same steps above anytime). 

To pause sharing (but remain on the pool), run the following command:

```bash
kalavai pool pause
```

When you are ready to resume sharing, run:
```bash
kalavai pool resume
```

To stop and leave the pool, run the following:

```bash
kalavai pool stop
```


## FAQs

### Something isn't right

Growing pains! Please report any issues in our [github repository](https://github.com/kalavai-net/kalavai-client/issues).


### Can I join (and leave) whenever I want?

Yes, you can, and we won't hold a grudge if you need to use your computer. You can pause or quit altogether as indicated [here](#stop-sharing).

### What is in it for me?

If you decide to share your compute with BOINC, you will gather credits in Kalavai, which will be redeemable for computing in any other public pool (this feature is coming really soon).

### Is my GPU constantly being used?

No. BOINC projects upload tasks to be completed to a queue, which volunteers computers poll for work. If there is no suitable work to be done by the worker, the machine will remain idle and no resources are spent.

If at any point you need your machine back, [pause or stop sharing](#stop-sharing) and come back when you are free.


### How do I check how much have I contributed?

Kalavai pools all the machines together and contributes to BOINC as a single entity. You can check how much the pool has shared overtime through the [Science United leaderboard page](https://scienceunited.org/su_lb.php) -look out for `Kalavai.net` entry.

![BOINC leaderboard](/docs/docs/assets/images/boinc_leaderboard.png)

Individual users can also check how much compute have they contributed via their home page in our [platform](https://platform.kalavai.net). Once you are logged in, click on the button displaying your user name on the left panel. This view will show how much of each key resource you have contributed thus far (CPUs, RAM, GPU).

![BOINC shared resources](/docs/docs/assets/images/boinc_shared.png)
