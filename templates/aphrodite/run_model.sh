
while [ $# -gt 0 ]; do
  case "$1" in
    --model_filename=*)
      model_filename="${1#*=}"
      ;;
    --repo_id=*)
      repo_id="${1#*=}"
      ;;
    --quantization=*)
      quantization="${1#*=}"
      ;;
    --tensor_parallel_size=*)
      tensor_parallel_size="${1#*=}"
      ;;
    --pipeline_parallel_size=*)
      pipeline_parallel_size="${1#*=}"
      ;;
    --extra=*)
      extra="${1#*=}"
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
if [ $model_filename = "None" ]; then
    # load from repo
    #python3 /vllm-workspace/download_hf.py --repo_id $repo_id --local_dir /vllm-workspace/

    python -m aphrodite.endpoints.openai.api_server  \
        --model $repo_id \
        --port 8080 --host 0.0.0.0 \
        --tensor-parallel-size $tensor_parallel_size \
        --pipeline-parallel-size $pipeline_parallel_size \
        $extra
else
    # load from file
    python /vllm-workspace/download_hf.py --repo_id $repo_id --filename $model_filename --local_dir /vllm-workspace/
    python -m aphrodite.endpoints.openai.api_server  \
        --model /vllm-workspace/$model_filename \
        --port 8080 --host 0.0.0.0 \
        --tensor-parallel-size $tensor_parallel_size \
        --pipeline-parallel-size $pipeline_parallel_size \
        $extra
fi

