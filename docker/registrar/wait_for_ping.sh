#!/bin/bash
# waits for servers to be reachable via ping
while [ $# -gt 0 ]; do
  case "$1" in
    --servers=*)
      servers="${1#*=}"
      ;;
    --count=*)
      count="${1#*=}"
      ;;
    --interval=*)
      interval="${1#*=}"
      ;;
    *)
      printf ""
      exit 1
  esac
  shift
done

# Set defaults
count=${count:-1}
interval=${interval:-15}

####################
# wait for hosts #
####################
IFS=',' read -r -a workers <<< "$servers" # split comma-separated list into array
for worker in "${workers[@]}"
do
    if [ -z $worker ]; then
      continue
    fi
    echo "Waiting for $worker to be reachable via ping..."
    #waiting for Worker $worker to be reachable...
    while ! ping -c $count $worker >/dev/null 2>&1
    do
        echo "...Not reachable, backoff ($interval seconds)"
        sleep $interval
    done
    echo "$worker is reachable!"
    sleep $interval
done
