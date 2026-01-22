#!/bin/bash

flannel_iface=""
extra=""
node_ip="0.0.0.0"
node_name=$HOSTNAME
user_id=""
random_suffix=""
mtu=""
token=""
tls_san=""

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
    --random_suffix=*)
      random_suffix="${1#*=}"
      ;;
    --extra=*)
      extra="${1#*=}"
      ;;
    --mtu=*)
      mtu="${1#*=}"
      ;;
    --tls_san=*)
      tls_san="${1#*=}"
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
if [ -z "${random_suffix}" ]; then
  random_suffix=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 6)
fi

node_name="${node_name}-${random_suffix}"

if [ ! -z "${flannel_iface}" ]; then
    while [ true ]; do
        if [ -d "/sys/class/net/$flannel_iface" ]; then
            node_ip=$(ifconfig $flannel_iface | grep 'inet ' | awk '{gsub(/^addr:/, "", $2); print $2}')
            # check the ip was set (it may take a while to do so)
            if [ ! -z "${node_ip}" ]; then
              echo "Interface exists: $node_ip"
              break
            else
              echo "Interface exists, IP still not set..."
            fi
        else
            echo "Interface not found. Retrying in 10 seconds..."
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 10
    done
    iface_server="--flannel-backend wireguard-native --flannel-iface "$flannel_iface
    iface_worker="--flannel-iface "$flannel_iface
    
fi

if [ ! -z "${user_id}" ]; then
    user_id="--node-label kalavai.cluster.user="$user_id
fi

sleep 5

# set MTU limitations
if [ ! -z "${mtu}" ]; then
  echo "Setting MTU limits..."
  # Loop through all interfaces
  for iface in $(ls /sys/class/net); do
      type=$(cat /sys/class/net/$iface/type)
      state=$(cat /sys/class/net/$iface/operstate)

      # Skip if it's a loopback (type 772) or not up
      if [ "$type" -eq 772 ]; then
          echo "Skipping $iface (loopback)"
          continue
      fi
      echo "Setting MTU $mtu on $iface (state: $state)"
      ip link set mtu "$mtu" dev "$iface"
  done
  #ip link set mtu $mtu $flannel_iface
  ifconfig
  sleep 10
fi

# For load balancers, set tls-san address
if [ ! -z "${tls_san}" ]; then
  tls_san="--tls-san "$tls_san
fi

echo "flannel iface: "$iface_server" ($node_ip)"
if [[ "$command" == "server" ]]; then
  # server agent
      # --kube-controller-manager-arg=node-monitor-grace-period=2m \
      # --kube-controller-manager-arg=node-monitor-period=2m \
      # --kubelet-arg=node-status-update-frequency=1m \
  exec /bin/k3s $command \
    --node-ip $node_ip \
    --cluster-init \
    --advertise-address $node_ip \
    --bind-address 0.0.0.0 \
    --node-external-ip $node_ip \
    --node-name $node_name \
    --service-node-port-range $port_range \
    $iface_server \
    --node-label gpu=$gpu \
    $user_id \
    $tls_san \
    $extra
elif [[ "$command" == "seed" ]]; then
  # extra control-plane servers
  if [ -z "$token" ]; then
    printf "[ERROR]: Token must be set for $command nodes"
    exit 1
  fi
  # add tls-san=LOAD_BALANCER_IP when using load balancer
  exec /bin/k3s server \
    --node-ip $node_ip \
    --server $server_ip \
    --advertise-address $node_ip \
    --bind-address 0.0.0.0 \
    --node-external-ip $node_ip \
    --node-name $node_name \
    --token $token \
    $iface_server \
    --node-label gpu=$gpu \
    $user_id \
    $tls_san \
    $extra
else
  # worker agent
      #--kubelet-arg=node-status-update-frequency=1m \
  if [ -z "$token" ]; then
    printf "[ERROR]: Token must be set for $command nodes"
    exit 1
  fi
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
