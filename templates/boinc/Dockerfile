#https://hub.docker.com/r/boinc/client
#https://github.com/diy-forge/boinc-kubernetes/blob/main/boinc_client.yaml

FROM boinc/client:base-ubuntu

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y iputils-ping

WORKDIR /workspace

COPY setup_workers.sh .
COPY wait_for_hosts.sh .
COPY merge.sh .

RUN chmod +x /workspace/merge.sh
RUN chmod +x /workspace/setup_workers.sh
RUN chmod +x /workspace/wait_for_hosts.sh

WORKDIR /var/lib/boinc
