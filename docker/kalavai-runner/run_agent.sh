#!/bin/bash

flannel_iface=""
extra=""
node_ip="0.0.0.0"

while [ $# -gt 0 ]; do
  case "$1" in
    --command=*)
      command="${1#*=}"
      ;;
    --port_range=*)
      port_range="${1#*=}"
      ;;
    --flannel_iface=*)
      flannel_iface="${1#*=}"
      ;;
    --server_ip=*)
      server_ip="${1#*=}"
      ;;
    --node_ip=*)
      node_ip="${1#*=}"
      ;;
    --token=*)
      token="${1#*=}"
      ;;
    --gpu=*)
      gpu="${1#*=}"
      ;;
    --extra=*)
      extra="${1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

# wait for network interface to be available (if set)
iface=""

if [ ! -z "${flannel_iface}" ]; then
    while [ true ]; do
        if [ -d "/sys/class/net/$flannel_iface" ]; then
            node_ip=$(ifconfig $flannel_iface | grep 'inet ' | awk '{gsub(/^addr:/, "", $2); print $2}')
            echo "Interface exists: $node_ip"
            break
        else
            echo "Interface not found. Retrying in 10 seconds..."
            RETRY_COUNT=$((RETRY_COUNT + 1))
            sleep 10
        fi
    done
    iface="--flannel-iface "$flannel_iface
    
fi

echo "flannel iface: "$iface" ($node_ip)"
sleep 10

if [[ "$command" == "server" ]]; then
    # server agent
    exec /bin/k3s $command \
        --kube-controller-manager-arg=node-monitor-grace-period=2m \
        --kube-controller-manager-arg=node-monitor-period=2m \
        --kubelet-arg=node-status-update-frequency=1m \
        --node-external-ip $node_ip \
        --service-node-port-range $port_range \
        $iface \
        --node-label gpu=$gpu \
        $extra
else
    # worker agent
    exec /bin/k3s $command \
        --kubelet-arg=node-status-update-frequency=1m \
        --node-external-ip $node_ip \
        --server $server_ip \
        --token $token \
        $iface \
        --node-label gpu=$gpu \
        $extra
fi