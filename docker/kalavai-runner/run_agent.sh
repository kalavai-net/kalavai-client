#!/bin/bash

flannel_iface=""
extra=""
node_ip="0.0.0.0"
node_name=$HOSTNAME
user_id=""

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
    --node_name=*)
      node_name="${1#*=}"
      ;;
    --token=*)
      token="${1#*=}"
      ;;
    --gpu=*)
      gpu="${1#*=}"
      ;;
    --user_id=*)
      user_id="${1#*=}"
      ;;
    --extra=*)
      extra="${1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "** Invalid argument: $1 ***\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

# wait for network interface to be available (if set)
iface_server=""
iface_worker=""

# add random tail to node name to avoid clashes
random_tail=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 6)
node_name="${node_name}-${random_tail}"

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
    iface_server="--flannel-backend wireguard-native --flannel-iface "$flannel_iface
    iface_worker="--flannel-iface "$flannel_iface
    
fi

if [ ! -z "${user_id}" ]; then
    user_id="--node-label kalavai.cluster.user="$user_id
fi

sleep 10

if [[ "$command" == "server" ]]; then
    # server agent
        # --kube-controller-manager-arg=node-monitor-grace-period=2m \
        # --kube-controller-manager-arg=node-monitor-period=2m \
        # --kubelet-arg=node-status-update-frequency=1m \
    echo "flannel iface: "$iface_server" ($node_ip)"
    exec /bin/k3s $command \
        --node-ip $node_ip \
        --advertise-address $node_ip \
        --bind-address 0.0.0.0 \
        --node-external-ip $node_ip \
        --node-name $node_name \
        --service-node-port-range $port_range \
        $iface_server \
        --node-label gpu=$gpu \
        $user_id \
        $extra
else
    # worker agent
    echo "flannel iface: "$iface_worker" ($node_ip)"
        #--kubelet-arg=node-status-update-frequency=1m \
    exec /bin/k3s $command \
        --node-external-ip $node_ip \
        --node-ip $node_ip \
        --bind-address 0.0.0.0 \
        --server $server_ip \
        --token $token \
        --node-name $node_name \
        $user_id \
        $iface_worker \
        --node-label gpu=$gpu \
        $extra
fi
