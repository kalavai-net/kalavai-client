#!/bin/bash

subcommand=$1
shift

ray_port=6379
ray_init_timeout=360000
ray_object_store_memory=4000000000
ray_block=""
ray_temp_dir="/tmp/ray"

round() {
  printf "%.${2}f" "${1}"
}

source /home/ray/workspace/env/bin/activate

case "$subcommand" in
  worker)
    ray_address=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --ray_address=*)
          ray_address="${1#*=}"
          ;;
        --ray_object_store_memory=*)
          ray_object_store_memory="${1#*=}"
          ;;
        --ray_block=*)
          ray_block="--block"
          ;;
        --ray_port=*)
          ray_port="${1#*=}"
          ;;
        --ray_init_timeout=*)
          ray_init_timeout="${1#*=}"
          ;;
        --ray_temp_dir=*)
          ray_temp_dir="${1#*=}"
          ;;
        *)
          echo "unknown argument: $1"
          exit 1
      esac
      shift
    done

    if [ -z "$ray_address" ]; then
      echo "Error: Missing argument --ray_address"
      exit 1
    fi

    for (( i=0; i < $ray_init_timeout; i+=5 )); do
      memory=$(echo "$ray_object_store_memory*0.75" | bc -l)
      round_mem=$(round ${memory} 0)
      RAY_BACKEND_LOG_LEVEL=error ray start --address=$ray_address:$ray_port $ray_block --temp-dir=$ray_temp_dir --object-store-memory=$round_mem
      if [ $? -eq 0 ]; then
        echo "Worker: Ray runtime started with head address $ray_address:$ray_port"
        exit 0
      fi
      echo "Waiting until the ray worker is active..."
      sleep 5s;
    done
    echo "Ray worker starts timeout, head address: $ray_address:$ray_port"
    exit 1
    ;;

  leader)
    ray_cluster_size=""
    while [ $# -gt 0 ]; do
          case "$1" in
            --ray_port=*)
              ray_port="${1#*=}"
              ;;
            --ray_object_store_memory=*)
              ray_object_store_memory="${1#*=}"
              ;;
            --ray_block=*)
              ray_block="--block"
              ;;
            --ray_cluster_size=*)
              ray_cluster_size="${1#*=}"
              ;;
            --ray_init_timeout=*)
              ray_init_timeout="${1#*=}"
              ;;
            --ray_temp_dir=*)
              ray_temp_dir="${1#*=}"
              ;;
            *)
              echo "unknown argument: $1"
              exit 1
          esac
          shift
    done

    if [ -z "$ray_cluster_size" ]; then
      echo "Error: Missing argument --ray_cluster_size"
      exit 1
    fi

    # start the ray daemon
    memory=$(echo "$ray_object_store_memory*0.75" | bc -l)
    round_mem=$(round ${memory} 0)
    RAY_BACKEND_LOG_LEVEL=error ray start --head --port=$ray_port --temp-dir=$ray_temp_dir --object-store-memory=$round_mem $ray_block

    # wait until all workers are active
    for (( i=0; i < $ray_init_timeout; i+=5 )); do
        active_nodes=`python3 -c 'import ray; ray.init(); print(sum(node["Alive"] for node in ray.nodes()))'`
        if [ $active_nodes -eq $ray_cluster_size ]; then
          echo "All ray workers are active and the ray cluster is initialized successfully."
          exit 0
        fi
        echo "Wait for all ray workers to be active. $active_nodes/$ray_cluster_size is active"
        sleep 5s;
    done

    echo "Waiting for all ray workers to be active timed out."
    exit 1
    ;;

  *)
    echo "unknown subcommand: $subcommand"
    exit 1
    ;;
esac