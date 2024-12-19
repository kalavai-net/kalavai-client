#!/bin/bash
# Converts a text list of rpc server addresses (one on each new line) 
# to a string of RPC server addresses, comma separated
while [ $# -gt 0 ]; do
  case "$1" in
    --rpc_servers=*)
      rpc_servers="${1#*=}"
      ;;
    --rpc_port=*)
      rpc_port="${1#*=}"
      ;;
    *)
      printf ""
      exit 1
  esac
  shift
done

####################
# wait for workers #
####################
rpc_servers=`sed ':a;N;$!ba;s/\n/;/g' <<< "$rpc_servers"` #convert \n to ; between worker addresses
IFS=';' read -r -a workers <<< "$rpc_servers" # split into array
rpc_workers=()
for worker in "${workers[@]}"
do
    if [ -z $worker ]; then
      continue
    fi
    #waiting for Worker $worker RPC to be up...
    while ! [[ $(wget -O - --tries 1 "$worker:$rpc_port" 2>&1) == *'connected'* ]]
    do
       sleep 10
    done
    # convert host addresses to RPC worker address
    rpc_workers+=("${worker}:$rpc_port")
done

function join_by {
  local d=${1-} f=${2-}
  if shift 2; then
    printf %s "$f" "${@/#/$d}"
  fi
}
worker_addresses=$(join_by , "${rpc_workers[@]}")
echo "${worker_addresses[*]}"