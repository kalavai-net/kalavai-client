"""
Extracts model id from a model in LiteLLM API
"""

import argparse
import requests
from urllib.parse import urljoin


def make_request(method, base_url, endpoint, headers):
    response = requests.request(
        method,
        urljoin(base_url, endpoint),
        headers=headers
    )
    data = response.json()
    return data

def extract_model_id(model_name, models):
    for model in models:
        if model["model_name"] == model_name:
            return model["model_info"]["id"]
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--litellm_url")
    parser.add_argument("--api_key", default="sk-1234")
    parser.add_argument("--model_name")

    args = parser.parse_args()    
    response = make_request(
        method="get",
        base_url=args.litellm_url,
        endpoint="/v1/model/info",
        headers={'x-goog-api-key': args.api_key}
    )
    # parse response to find model_name id
    print(
        extract_model_id(model_name=args.model_name, models=response["data"])
    )
