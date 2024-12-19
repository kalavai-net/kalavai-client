#!/bin/bash
# Converts a text list of rpc server addresses (one on each new line) 
# to a string of RPC server addresses, comma separated
while [ $# -gt 0 ]; do
  case "$1" in
    --workers=*)
      workers="${1#*=}"
      ;;
    --boinc_password=*)
      boinc_password="${1#*=}"
      ;;
    --email=*)
      email="${1#*=}"
      ;;
    --password=*)
      password="${1#*=}"
      ;;
    *)
      printf ""
      exit 1
  esac
  shift
done

######################
# search for workers #
######################
workers=`sed ':a;N;$!ba;s/\n/;/g' <<< "$workers"` #convert \n to ; between worker addresses
IFS=';' read -r -a addresses <<< "$workers" # split into array
while :
do
  for worker in "${addresses[@]}"
  do
      sleep 1
      if [ -z $worker ]; then
        continue
      fi
      if ! ping -c 1 -n $worker > /dev/null
      then
        continue
      fi
      echo "Worker ($worker) is up. Setting project..."
      if [[ $(boinccmd --host $worker --passwd $boinc_password --acct_mgr info 2>&1) == *'https://scienceunited.org'* ]]
      then
        # do nothing, worker already setup
        echo $worker" is ready"
        sleep 10
      else
        # connect and configure
        # retry if requested
        while [[ $(boinccmd --host $worker --passwd $boinc_password --acct_mgr attach https://scienceunited.org $email $password 2>&1) == *'retry'* ]]
        do
            sleep 10
        done
      fi
  done
done
