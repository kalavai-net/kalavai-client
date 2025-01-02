#!/bin/bash

while [ $# -gt 0 ]; do
  case "$1" in
    --model_id=*)
      model_id="${1#*=}"
      ;;
    # --local_dir=*)
    #   local_dir="${1#*=}"
    #   ;;
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

echo $model_id" downloading..."
python /home/ray/workspace/download_hf.py \
  --repo_id $model_id \
  --local_dir $remote_dir/$model_id

# check if model is already present
# result=$(HF_HOME=$remote_dir huggingface-cli scan-cache -v | grep "$model_id")
# if [ -z "${result}" ];
# then
#     echo $model_id" not present, downloading..."
#     # model is not present, download
#     # This workaround is required since it is not currently possible to download
#     # models directly to s3 bucket (but it is possible to copy them over)
#     HF_HOME=$local_dir huggingface-cli download $model_id --quiet
#     cp -L -r $local_dir/* $remote_dir/
#     rm -r $local_dir/*
# else
#     echo "present"
# fi
