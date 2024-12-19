#!/bin/bash

while [ $# -gt 0 ]; do
  case "$1" in
    --cpu-workers=*)
      cpu_workers="${1#*=}"
      ;;
    --gpu-workers=*)
      gpu_workers="${1#*=}"
      ;;
    --output=*)
      output="${1#*=}"
      ;;
    *)
      printf "Error\n"
      exit 1
  esac
  shift
done
# Merge address files
c=`cat $cpu_workers`
g=`cat $gpu_workers`
echo "$c $g" | tr " " "\n" > $output