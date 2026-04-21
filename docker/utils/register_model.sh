#!/bin/bash

cache_dir="/cache"
job_id="None"
api_key="DUMMY"
litellm_kalavai_extras="{}"
model_info="{}"
return="no"
rpm_limit="50000"

while [ $# -gt 0 ]; do
  case "$1" in
    --litellm_base_url=*)
      litellm_base_url="${1#*=}"
      ;;
    --litellm_key=*)
      litellm_key="${1#*=}"
      ;;
    --litellm_model_name=*)
      litellm_model_name="${1#*=}"
      ;;
    --litellm_kalavai_extras=*)
      litellm_kalavai_extras="${1#*=}"
      ;;
    --model_id=*)
      model_id="${1#*=}"
      ;;
    --provider=*)
      provider="${1#*=}"
      ;;
    --api_base=*)
      api_base="${1#*=}"
      ;;
    --api_key=*)
      api_key="${1#*=}"
      ;;
    --job_id=*)
      job_id="${1#*=}"
      ;;
    --model_info=*)
      model_info="${1#*=}"
      ;;
    --rpm_limit=*)
      rpm_limit="${1#*=}"
      ;;
    --return=*)
      return="yes"
      ;;
    *)
      printf "*****************************************\n"
      printf "* register_model.sh: Invalid argument: $1\n"
      printf "*****************************************\n"
      exit 1
  esac
  shift
done

echo ">>> Registering model with LiteLLM"

echo "----------------------------------------"
echo "LiteLLM Base URL: "$litellm_base_url
echo "LiteLLM Key: "$litellm_key
echo "LiteLLM Model Name: "$litellm_model_name
echo "LiteLLM Kalavai Extras: "$litellm_kalavai_extras
echo "Model Info: "$model_info
echo "Job ID: "$job_id
echo "----------------------------------------"


json_payload=$(cat <<EOF
{
  "model_name": "$litellm_model_name",
  "model_info": $model_info,
  "litellm_params": {
    "drop_params": false,
    "model": "$provider/$model_id",
    "api_base": "$api_base",
    "api_key": "$api_key",
    "job_id": "$job_id",
    "rpm": "$rpm_limit",
    "extras": $litellm_kalavai_extras
  }
}
EOF
)

echo "JSON payload: "$json_payload

# Retry mechanism with exponential backoff
max_retries=3
retry_delay=5
attempt=1
success=false

while [ $attempt -le $max_retries ] && [ "$success" = false ]; do
    echo "Attempt $attempt of $max_retries..."
    
    # Make the API call with timeout
    result=$(curl -X POST "$litellm_base_url/model/new" \
        -H "Authorization: Bearer $litellm_key" \
        -H "accept: application/json" \
        -H "Content-Type: application/json" \
        -d "$json_payload" \
        --connect-timeout 30 \
        --max-time 60 \
        --silent \
        --write-out "\nHTTP_CODE:%{http_code}\nCURL_CODE:%{exitcode}\n" \
        2>&1)
    
    curl_exit_code=$?
    
    # Extract HTTP code and curl code from result
    http_code=$(echo "$result" | grep "HTTP_CODE:" | cut -d: -f2)
    curl_code=$(echo "$result" | grep "CURL_CODE:" | cut -d: -f2)
    response_body=$(echo "$result" | grep -v "HTTP_CODE:" | grep -v "CURL_CODE:")
    
    echo "HTTP Status Code: $http_code"
    echo "CURL Exit Code: $curl_code"
    echo "Response: $response_body"
    
    # Check for success conditions
    if [ "$curl_code" = "0" ] && [ "$http_code" = "200" ]; then
        # Additional check: verify response contains success indicators
        if echo "$response_body" | grep -q -E "(success|registered|created|ok)" || echo "$response_body" | grep -q -v -E "(error|fail|timeout|gateway)"; then
            success=true
            echo "Model registered successfully!"
            echo "$response_body"
            if [ "$return" = "no" ]; then
                tail -f /dev/null
            fi
            exit 0
        else
            echo "Response received but appears to contain error indicators"
        fi
    else
        echo "Request failed - HTTP: $http_code, CURL: $curl_code"
        
        # Check for specific error patterns
        if echo "$response_body" | grep -qi -E "(timeout|gateway timeout|connection timeout)"; then
            echo "Timeout detected - will retry"
        elif echo "$response_body" | grep -qi -E "(gateway|502|503|504)"; then
            echo "Gateway error detected - will retry"
        elif [ "$http_code" -ge 500 ]; then
            echo "Server error detected - will retry"
        else
            echo "Client error or unrecoverable error detected"
            if [ $attempt -eq $max_retries ]; then
                echo "Max retries reached with client error - giving up"
                echo "$response_body"
                exit 1
            fi
        fi
    fi
    
    if [ "$success" = false ] && [ $attempt -lt $max_retries ]; then
        echo "Waiting ${retry_delay}s before retry..."
        sleep $retry_delay
        retry_delay=$((retry_delay * 2))  # Exponential backoff
    fi
    
    attempt=$((attempt + 1))
done

if [ "$success" = false ]; then
    echo "Failed to register model after $max_retries attempts"
    echo "Last response: $response_body"
    exit 1
fi
