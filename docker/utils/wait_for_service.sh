#!/bin/bash
# waits for a service in host(s) to be ready
while [ $# -gt 0 ]; do
  case "$1" in
    --servers=*)
      servers="${1#*=}"
      ;;
    --port=*)
      port="${1#*=}"
      ;;
    *)
      printf ""
      exit 1
  esac
  shift
done

####################
# wait for host #
####################
servers=`sed ':a;N;$!ba;s/\n/;/g' <<< "$servers"` #convert \n to ; between worker addresses
IFS=';' read -r -a workers <<< "$servers" # split into array
rpc_workers=()
for worker in "${workers[@]}"
do
    if [ -z $worker ]; then
      continue
    fi
    echo "Waiting for $worker:$port..."
    #waiting for Worker $worker RPC to be up...
    while ! [[ $(wget -O - --tries 1 "$worker:$port" 2>&1) == *'connected'* ]]
    do
        echo "...Not ready, backoff"
        sleep 30
    done
done
