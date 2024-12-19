#!/bin/bash
while [ $# -gt 0 ]; do
  case "$1" in
    --hosts=*)
      hosts="${1#*=}"
      ;;
    *)
      printf ""
      exit 1
  esac
  shift
done

##################
# wait for hosts #
##################
hosts=`sed ':a;N;$!ba;s/\n/;/g' <<< "$hosts"` #convert \n to ; between worker addresses
IFS=';' read -r -a addresses <<< "$hosts" # split into array
for host in "${addresses[@]}"
do
    if [ -z $host ]; then
      continue
    fi
    echo "Waiting for host ($host) to be up..."
    while ! ping -c 1 -n $host > /dev/null
    do
       sleep 10
    done
done
echo "All hosts available"
