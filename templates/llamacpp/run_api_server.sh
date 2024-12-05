#!/bin/bash

local_dir=/tmp
port=50052
extra=""

while [ $# -gt 0 ]; do
  case "$1" in
    --repo_id=*)
      repo_id="${1#*=}"
      ;;
    --model_filename=*)
      model_filename="${1#*=}"
      ;;
    --local_dir=*)
      local_dir="${1#*=}"
      ;;
    --rpc_servers=*)
      rpc_servers="${1#*=}"
      ;;
    --rpc_port=*)
      rpc_port="${1#*=}"
      ;;
    --port=*)
      port="${1#*=}"
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

source /workspace/env/bin/activate

#################
# dowload model #
#################
huggingface-cli download \
    $repo_id \
    $model_filename \
    --local-dir $local_dir \
    --local-dir-use-symlinks False
  
####################
# wait for workers #
####################
rpc_servers=`sed ":a;N;s/\n/;/g" <<< "$rpc_servers"` #convert \n to ; between worker addresses
IFS=';' read -r -a workers <<< "$rpc_servers" # split into array
echo "Waiting for RPC SERVERS: "$workers
for worker in "${workers[@]}"
do
    printf "%s" "waiting for Worker $worker..."
    while ! ping -c 2 -n $worker > /dev/null
    do
        printf "%c" "."
    done
    printf "\n%s\n"  "$worker is online"
done
# convert host addresses to RPC worker addresses
rpc_workers=()
for E in "${workers[@]}"; do
    rpc_workers+=("${E}:$rpc_port")
done

function join_by {
  local d=${1-} f=${2-}
  if shift 2; then
    printf %s "$f" "${@/#/$d}"
  fi
}
rpc_workers=$(join_by , "${rpc_workers[@]}")

##################
# run API server #
##################
for i in {0..10}
do
  python -m llama_cpp.server \
      --model $local_dir/$model_filename \
      --rpc_servers $rpc_workers \
      --port $port \
      --host 0.0.0.0 \
      $extra
  # backoff
  sleep $((10*"$i"))
done

