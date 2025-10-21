"""
Marks a model as obsolete in LiteLLM API
- Adds deletion date
- Sets access group to none
"""

import argparse
import requests
from urllib.parse import urljoin
import datetime
import json


def make_request(method, base_url, endpoint, api_key=None, **kwargs):
    headers={'x-goog-api-key': api_key}
    response = requests.request(
        method,
        urljoin(base_url, endpoint),
        headers=headers,
        **kwargs
    )
    data = response.json()
    return data

def extract_model_id(model_name, models, job_id=None):
    for model in models:
        if model["model_name"] == model_name:
            if job_id is None:
                return model["model_info"]["id"]
            else:
                if "job_id" not in model["litellm_params"]:
                    continue
                if job_id == model["litellm_params"]["job_id"]:
                    return model["model_info"]["id"]
    return None

def get_model_info(litellm_url, api_key, job_id):
    """
    Get the model info from LiteLLM
    """
    response = make_request(
        method="GET",
        base_url=litellm_url,
        endpoint=f"/v1/model/info",
        api_key=api_key
    )
    for model_info in response["data"]:
        if "job_id" in model_info["litellm_params"] and model_info["litellm_params"]["job_id"] == job_id:
            if "extras" in model_info["litellm_params"] and "deleted_at" in model_info["litellm_params"]["extras"]:
                continue
            return model_info

def update_model(litellm_url, api_key, model_id,model):
    response = make_request(
        method="PATCH",
        base_url=litellm_url,
        endpoint=f"/model/{model_id}/update",
        api_key=api_key,
        json=model
    )
    return response


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--litellm_url")
    parser.add_argument("--api_key", default="sk-1234")
    parser.add_argument("--job_id", default=None)
    args = parser.parse_args()

    model = get_model_info(litellm_url=args.litellm_url, api_key=args.api_key, job_id=args.job_id)
    if model is None:
        print("Model not found")
        exit(1)
    model_id = model["model_info"]["id"]
    # mark model as obsolete:
    #   add deletion date
    #   set to none access group
    model["model_info"]["access_groups"] = ["none"]
    model["litellm_params"]["extras"]["deleted_at"] = datetime.datetime.now().isoformat()

    # update model
    response = update_model(litellm_url=args.litellm_url, api_key=args.api_key, model_id=model_id, model=model)
    print(response)

    # response = make_request(
    #     method="get",
    #     base_url=args.litellm_url,
    #     endpoint="/v1/model/info",
    #     api_key=args.api_key
    # )
    # # parse response to find model_name id
    # print(
    #     extract_model_id(model_name=args.model_name, models=response["data"], job_id=args.job_id)
    # )
