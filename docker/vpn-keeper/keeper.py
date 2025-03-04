"""
Utility to keep hosts alive in netmaker VPN

Server survey

for node in GET /api/nodes
    if node[connected] and fails ping:
        PUT api/hosts/node[hostid]/keys to update keys on host
        print action

API Documentation: https://docs.netmaker.io/api
"""
import requests
import os
import time
import datetime
import ipaddress


API_URL = os.getenv("API_URL", "https://api.netmaker.kalavai.net")
API_KEY = os.getenv("API_KEY", "XXXXX")
SUBNET = os.getenv("SUBNET", "100.10.0.0/16")
ALIVE_CUTOFF = 300


def log_message(message):
    print(f"[{datetime.datetime.now()}] {message}")

def server_request(method, endpoint):
    try:
        response = requests.request(
            method=method,
            url=f"{API_URL}{endpoint}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        response.raise_for_status()
    except Exception as e:
        log_message(message=f"Error in request {endpoint}: {str(e)}")
        return {}
    try:
        return response.json()
    except:
        return {response.text}

def ping(host):
    return os.system(f"ping -c 5 {host} >/dev/null 2>&1") == 0

def is_alive(lastcheckin):
    diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(lastcheckin)
    return diff.total_seconds() < ALIVE_CUTOFF


def main():
    while True:
        # Get all nodes
        nodes = server_request(
            method="get",
            endpoint="/api/nodes")
        for node in nodes:
            address = node["address"][:node["address"].index("/")]
            if ipaddress.ip_address(address) not in ipaddress.ip_network(SUBNET):
                # skip addresses not in expected host subnet
                continue
            if is_alive(node["lastcheckin"]) and not ping(address):
                result = server_request(
                    method="put",
                    endpoint=f"/api/hosts/{node['hostid']}/keys")
                #result = {}
                log_message(message=f"Updated keys for {address}: {result}")
        
        time.sleep(10)


if __name__ == "__main__":
    main()
