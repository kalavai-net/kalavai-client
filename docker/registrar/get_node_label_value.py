import json
import argparse
from kubernetes import client, config


def get_node_label_values(
    node_name,
    label_key,
    in_cluster=True
):
    if in_cluster:
        config.load_incluster_config()
    else:
        # Only works if this script is run by K8s as a POD
        config.load_kube_config()
    
    # Initialize the CoreV1 API client
    v1 = client.CoreV1Api()
    
    try:
        kwargs = {"_preload_content": False}
        kwargs["label_selector"] = label_key
        response = v1.list_node(**kwargs)
        nodes_data = json.loads(response.data)
        
        return {
            node["metadata"]["name"]: {
                k: v for k, v in node["metadata"].get("labels", {}).items() if k == label_key
            }
            for node in nodes_data.get("items", []) if node["metadata"]["name"] == node_name
        }

    except client.exceptions.ApiException as e:
        print(f"Exception when calling CoreV1Api->read_node: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get node label values")
    parser.add_argument("--node-name", required=True, help="Node name")
    parser.add_argument("--label-key", required=True, help="Label key to check")
    parser.add_argument("--in-cluster", action="store_true", help="Run in cluster")

    args = parser.parse_args()
    
    node_data = get_node_label_values(
        node_name=args.node_name,
        label_key=args.label_key,
        in_cluster=args.in_cluster
    )

    print(node_data.get(args.node_name, {}).get(args.label_key, None))