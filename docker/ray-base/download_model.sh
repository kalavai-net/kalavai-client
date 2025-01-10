#!/bin/bash

while [ $# -gt 0 ]; do
  case "$1" in
    --model_id=*)
      model_id="${1#*=}"
      ;;
    --model_filename=*)
      model_filename="${1#*=}"
      ;;
    --remote_dir=*)
      remote_dir="${1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

source /home/ray/workspace/env/bin/activate

if [ -z "$model_filename" ]; then
  echo $model_id" downloading..."
  python /home/ray/workspace/download_hf.py \
    --repo_id $model_id \
    --local_dir $remote_dir/$model_id
else
  echo $model_id" -> "$model_filename" downloading..."
  python /home/ray/workspace/download_hf.py \
    --repo_id $repo_id \
    --filename $model_filename \
    --local_dir $remote_dir
fi
