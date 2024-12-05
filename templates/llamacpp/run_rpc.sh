#!/bin/bash

rpc_port=50052

while [ $# -gt 0 ]; do
  case "$1" in
    --rpc_port=*)
      rpc_port="${1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

/workspace/llama.cpp/bin/rpc-server -p $rpc_port -H 0.0.0.0
