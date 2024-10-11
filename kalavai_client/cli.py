from collections import defaultdict
import os
import uuid
from string import Template
import time
import socket
from pathlib import Path

import yaml
import netifaces as ni
import arguably
from rich.console import Console

from kalavai_client.utils import (
    user_path,
    decode_dict,
    generate_join_token,
    user_confirm,
    load_template,
    store_server_info,
    load_server_auth_key,
    load_node_name,
    load_server_ip,
    generate_table,
    request_to_server,
    get_all_templates,
    load_watcher_service_url,
    run_cmd,
    is_service_running,
    load_cluster_name,
    resource_path,
    user_path,
    safe_remove,
    join_vpn,
    load_net_token,
    leave_vpn
)
from kalavai_client.cluster import (
    k3sCluster
)


LOCAL_TEMPLATES_DIR = os.getenv("LOCAL_TEMPLATES_DIR", None)
VERSION = 1
RESOURCE_EXCLUDE = ["ephemeral-storage", "hugepages-1Gi", "hugepages-2Mi", "pods"]
CORE_NAMESPACES = ["lws-system", "kube-system", "gpu-operator", "kalavai"]
TEMPLATE_LABEL = "kalavai.lws.name"
KUBE_VERSION = os.getenv("KALAVAI_KUBE_VERSION", "v1.31.1+k3s1")
FLANNEL_IFACE = os.getenv("KALAVAI_FLANNEL_IFACE", None)
# kalavai templates
CLUSTER_CONFIG_TEMPLATE = resource_path("assets/seed.yaml")
HELM_APPS_FILE = resource_path("assets/apps.yaml")
SERVICE_TEMPLATE_FILE = resource_path("assets/service_template.yaml")
# user specific config files
USER_HELM_APPS_FILE = user_path("apps.yaml")
USER_LOCAL_CONFIG_FILE = user_path("cluster_config.conf")
USER_KUBECONFIG_FILE = user_path("kubeconfig")
USER_LOCAL_SERVER_FILE = user_path(".server")
USER_TEMPLATES_FOLDER = user_path("templates", create_path=True)


console = Console()
CLUSTER = k3sCluster(
    kube_version=KUBE_VERSION,
    flannel_iface=FLANNEL_IFACE,
    kubeconfig_file=USER_KUBECONFIG_FILE
)


######################
## HELPER FUNCTIONS ##
######################

def cleanup_local():
    # disconnect from private network
    vpns = leave_vpn()
    for vpn in vpns:
        console.log(f"You have left {vpn} VPN")
    safe_remove(USER_LOCAL_CONFIG_FILE)
    safe_remove(USER_KUBECONFIG_FILE)
    safe_remove(USER_LOCAL_SERVER_FILE)
    
    
def fetch_remote_templates():
    templates = get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR,
        remote_load=True)
    return templates

        
def restart():
    console.log("[white] Restarting sharing (may take a few minutes)...")
    success = CLUSTER.restart_agent()
    if success:
        console.log("[white] Kalava sharing resumed")
        fetch_remote_templates()
    else:
        console.log("[red] Error when restarting. Please run [yellow]kalavai restart[white] again.")

def check_gpu_drivers():
    value = run_cmd("command -v nvidia-smi")
    if len(value.decode("utf-8")) == 0:
        # no nvidia installed, no need to check nvidia any further
        return True
    else:
        # check drivers are set correctly
        try:
            value = run_cmd("nvidia-smi")
            return True
        except:
            console.log("[red] Nvidia not configured properly. Please check your drivers are installed and configured")
            console.log("[white] run [yellow]nvidia-smi[white] to see if the drivers can find your card.")
            return False

def set_schedulable(schedulable, node_name=load_node_name(USER_LOCAL_SERVER_FILE)):
    """
    Delete job in the cluster
    """
    # deploy template with kube-watcher
    data = {
        "schedulable": str(schedulable),
        "node_names": [node_name]
    }
    try:
        _ = request_to_server(
            method="post",
            endpoint="/v1/set_node_schedulable",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        console.log(f"[green] Success")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


def select_ip_address():
    ips = []
    for iface in ni.interfaces():
        try:
            ip = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
            ips.append(ip)
        except:
            pass
    while True:
        option = user_confirm(
            question="Select IP to advertise the node (needs to be visible to other nodes)",
            options=ips
        )
        if option is not None:
            break
        else:
            console.log("[red] Input error")
    return ips[option]


##################
## CLI COMMANDS ##
##################

@arguably.command
def start(cluster_name, *others,  ip_address: str=None, net_token: str=None):
    """
    Start Kalavai cluster and start/resume sharing resources.

    Args:
        *others: all the other positional arguments go here
    """

    # join private network if provided
    if net_token is not None:
        console.log("Joining private network")
        try:
            join_vpn(token=net_token)
            time.sleep(5)
        except Exception as e:
            console.log(f"[red]Error when joining network: {str(e)}")
            return

    if ip_address is None:
        console.log("Scanning for valid IPs...")
        ip_address = select_ip_address()
    console.log(f"Using {ip_address} address for server")

    auth_key = str(uuid.uuid4())
    watcher_port = 31000
    values = {
        "cluster_name": cluster_name,
        "server_address": ip_address,
        "auth_key": auth_key,
        "watcher_port": watcher_port
    }
    # populate cluster config file
    with open(CLUSTER_CONFIG_TEMPLATE, "r") as f:
        config = Template(f.read())
        config = config.substitute(values)
    
    with open(USER_LOCAL_CONFIG_FILE, "w") as f:
        f.write(config)
    
    # 1. start k3s server
    console.log("Installing cluster seed")
    CLUSTER.start_seed_node(
        ip_address=ip_address,
        cluster_config_file=USER_LOCAL_CONFIG_FILE)

    watcher_service = f"{ip_address}:{watcher_port}"
    store_server_info(
        server_ip=ip_address,
        auth_key=auth_key,
        file=USER_LOCAL_SERVER_FILE,
        watcher_service=watcher_service,
        node_name=socket.gethostname(),
        cluster_name=cluster_name,
        net_token=net_token)
    
    while not CLUSTER.is_agent_running():
        console.log("Waiting for seed to start...")
        time.sleep(10)
    
    console.log("Install dependencies...")
    # set template values in helmfile
    with open(HELM_APPS_FILE, "r") as f:
        config = Template(f.read())
        config = config.substitute(values)
    
    with open(USER_HELM_APPS_FILE, "w") as f:
        f.write(config)
    CLUSTER.install_dependencies(
        dependencies_file=USER_HELM_APPS_FILE
    )
    
    console.log("[green]Your cluster is ready! Grow your cluster by sharing your joining token with others. Run [yellow]kalavai token[green] to generate one.")
    fetch_remote_templates()
    return None

@arguably.command
def token(*others):
    """
    Generate a join token for others to connect to your cluster
    """
    if not Path(USER_LOCAL_CONFIG_FILE).is_file():
        console.log("[red]Local config file not found. Possible reasons: the cluster has not been started or this is a worker node.")
        return None
    
    with open(USER_LOCAL_CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)
    
    auth_key = load_server_auth_key(USER_LOCAL_SERVER_FILE)
    watcher_service = load_watcher_service_url(USER_LOCAL_SERVER_FILE)
    net_token = load_net_token(USER_LOCAL_SERVER_FILE)

    cluster_token = CLUSTER.get_cluster_token()

    ip_address = config["spec"]["api"]["address"]
    cluster_name = config["metadata"]["name"]

    join_token = generate_join_token(
        cluster_ip=f"https://{ip_address}:6443",
        cluster_name=cluster_name,
        cluster_token=cluster_token,
        auth_key=auth_key,
        watcher_service=watcher_service,
        net_token=net_token
    )

    console.log("[green]Join token:")
    print(join_token)

    return join_token

@arguably.command
def check_token(token, *others):
    """
    Utility to check the validity of a join token
    """
    try:
        data = decode_dict(token)
        for field in ["cluster_ip", "cluster_token", "cluster_name", "auth_key", "watcher_service", "net_token"]:
            assert field in data
        console.log("[green]Token format is correct")
        return True
    except Exception as e:
        console.log(f"[white]{str(e)}")
        console.log("[red]Token is invalid.")
        return False


@arguably.command
def join(token, *others, node_name=None, ip_address: str = None):
    """
    Join Kalavai cluster and start/resume sharing resources.

    Args:
        *others: all the other positional arguments go here
    """
    if node_name is None:
        node_name = socket.gethostname()
    
    # check token
    if not check_token(token):
        return

    try:
        data = decode_dict(token)
        kalavai_url = data["cluster_ip"]
        kalavai_token = data["cluster_token"]
        cluster_name = data["cluster_name"]
        auth_key = data['auth_key']
        watcher_service = data["watcher_service"]
        net_token = data["net_token"]
    except Exception as e:
        console.log(str(e))
        console.log("[red] Invalid token")
        return
    
    # join private network if provided
    if net_token is not None:
        console.log("Joining private network")
        try:
            join_vpn(token=net_token)
            time.sleep(5)
        except Exception as e:
            console.log(f"[red]Error when joining network: {str(e)}")
            return

    if ip_address is None:
        console.log("Scanning for valid IPs...")
        ip_address = select_ip_address()
    console.log(f"Using {ip_address} address for worker")
    
        
    # check that k3s is not running already in the host
    # k3s service running or preinstalled
    if  not CLUSTER.is_agent_running():
        # local k3s agent join
        console.log(f"[white] Connecting to {cluster_name} @ {kalavai_url} (this may take a few minutes)...")
        try:
            CLUSTER.start_worker_node(
                url=kalavai_url,
                token=kalavai_token,
                node_name=node_name,
                ip_address=ip_address)
        except Exception as e:
            console.log(f"[red] Error connecting to {cluster_name} @ {kalavai_url}. Check with the admin if the token is still valid.")
            exit()

        while not CLUSTER.is_agent_running():
            console.log("Waiting for worker to start...")
            time.sleep(10)
        store_server_info(
            server_ip=kalavai_url,
            auth_key=auth_key,
            file=USER_LOCAL_SERVER_FILE,
            watcher_service=watcher_service,
            node_name=node_name,
            cluster_name=cluster_name)
        fetch_remote_templates()
    else:
        console.log(f"[white] You are already connected to {load_cluster_name(USER_LOCAL_SERVER_FILE)}. Enter [yellow]kalavai stop[white] to exit and join another one.")
    
    if not CLUSTER.is_agent_running():
        restart()
    
    # set status to schedulable
    set_schedulable(schedulable=True)
    console.log(f"[green] You are connected to {cluster_name}")
            
    
@arguably.command
def stop(*others):
    """
    Stop sharing your device and clean up. DO THIS ONLY IF YOU WANT TO REMOVE KALAVAI-CLIENT from your device.

    Args:
        *others: all the other positional arguments go here
    """
    # k3s stop locally
    console.log("[white] Stopping kalavai app...")
    nodes__delete(load_node_name(USER_LOCAL_SERVER_FILE))
    CLUSTER.remove_agent()
    cleanup_local()
    console.log("[white] Kalavai has stopped sharing your resources. Use [yellow]kalavai start[white] or [yellow]kalavai join[white] to start again!")

@arguably.command
def pause(*others):
    """
    Pause sharing your device and make your device unavailable for kalavai scheduling.

    Args:
        *others: all the other positional arguments go here
    """
    # k3s stop locally
    console.log("[white] Pausing kalavai app...")
    success = CLUSTER.pause_agent()
    if success:
        console.log("[white] Kalava sharing paused. Resume with [yellow]kalavai resume")
    else:
        console.log("[red] Error when stopping. Please run [yellow]kalavai pause[red] again.")

@arguably.command
def resume(*others):
    """
    Resume sharing your device and make device available for kalavai scheduling.

    Args:
        *others: all the other positional arguments go here
    """
    # k3s stop locally
    if not CLUSTER.is_cluster_init():
        console.log("[red] Kalavai app was not started before, please run [yellow]kalavai start[red] to start a cluster or [yellow]kalavai join[red] to join one first")
        return
    console.log("[white] Resuming kalavai app...")
    restart()


@arguably.command
def resources(*others):
    """
    Display information about resources on the cluster
    """
    if not CLUSTER.is_cluster_init() or not CLUSTER.is_agent_running():
        console.log("[red]Kalavai is not running or not installed on your machine")
        return

    try:
        total = request_to_server(
            method="get",
            endpoint="/v1/get_cluster_total_resources",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        available = request_to_server(
            method="get",
            endpoint="/v1/get_cluster_available_resources",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        columns = []
        total_values = []
        available_values = []
        for col in total.keys():
            if col in RESOURCE_EXCLUDE:
                continue
            columns.append(col)
            total_values.append(str(total[col]))
            available_values.append(str(available[col]))
        
        columns = [""] + columns
        total_values = ["Total"] + total_values
        available_values = ["Available"] + available_values
        
        rows = [
            tuple(available_values),
            tuple(total_values)
        ]
        console.print(
            generate_table(columns=columns, rows=rows, end_sections=[0, 1])
        )
        
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")

@arguably.command
def status(*others):
    """
    Check the status of the kalavai cluster
    """
    try:
        response = request_to_server(
            method="POST",
            endpoint="/v1/get_deployments",
            data={"namespaces": CORE_NAMESPACES},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        global_status = True
        for _, deployments in response.items():
            for key, values in deployments.items():
                state = values["available_replicas"] == values["ready_replicas"]
                console.log(f"{key} status: {state}")
                global_status &= state
        console.log("---------------------------------")
        console.log(f"--> Cluster status: {global_status}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


@arguably.command
def diagnostics(*others, log_file=None):
    """
    Run diagnostics on a local installation of kalavai, and stores in log file
    * is k0s installed
    * is agent running
    * is kube-watcher running
    * is lws running
    """
    logs = []

    logs.append(f"App installed: {CLUSTER.is_cluster_init()}")

    logs.append(f"Agent running: {CLUSTER.is_agent_running()}")

    logs.append(f"Containerd running: {is_service_running(service='containerd.service')}")

    logs.append("Getting deployment status...")

    if CLUSTER.is_seed_node():
        # seed node
        data = CLUSTER.diagnostics()
        logs.append(data)
    else:
        # worker node
        logs.append("Could not access node info. This info is only available to seed nodes. Ignore if you are on a worker node.")

    if log_file is not None:
        with open(log_file, "w") as f:
            for log in logs:
                f.write(log)
                f.write("\n")
        console.log(f"[green]Logs written to {log_file}")
    else:
        for log in logs:
            console.log(f"{log}\n")

@arguably.command
def nodes__list(*others):
    """
    Display information about nodes connected
    """
    if not CLUSTER.is_cluster_init() or not CLUSTER.is_agent_running():
        console.log("[red]Kalavai is not running or not installed on your machine")
        return

    try:
        data = request_to_server(
            method="get",
            endpoint="/v1/get_nodes",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        rows = []
        columns = ["Node name"]
        for node, status in data.items():
            row = [node]
            for key, value in status.items():
                if key not in columns:
                    columns.append(key)
                row.append(str(value))
            rows.append(tuple(row))
        
        console.log("Nodes with 'unschedulable=True' will not receive workload")
        console.log("To make a node unschedulable (i.e. won't receive workloads) use [yellow]kalavai nodes cordon <node name>")
        console.log("To make a node schedulable (i.e. will receive workloads) use [yellow]kalavai nodes uncordon <node name>")
        console.print(
            generate_table(columns=columns, rows=rows)
        )
        
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


@arguably.command
def nodes__delete(name, *others):
    """
    Delete a node from the cluster
    """
    data = {
        "node_names": [name]
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/delete_nodes",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        console.log(f"Node {name} deleted successfully")
    except Exception as e:
        console.log(f"[yellow](ignore if stopping worker from dead server). Error when removing node {name}: {str(e)}")


@arguably.command
def nodes__cordon(node_name, *others):
    """
    Cordon a particular node so no more work will be scheduled on it
    """
    set_schedulable(schedulable=False, node_name=node_name)


@arguably.command
def nodes__uncordon(node_name, *others):
    """
    Uncordon a particular node to allow more work to be scheduled on it
    """
    set_schedulable(schedulable=True, node_name=node_name)


@arguably.command
def jobs__templates(*others):
    """
    Job templates integrated with kalavai. Use env var LOCAL_TEMPLATES_DIR to test local templates
    """
    templates = get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR)
    
    console.log("[green]Available templates:")
    for _, template in templates:
        console.log(f"[green]{template}")


@arguably.command
def jobs__reload(*others):
    """
    Refreshes template collection from remote repository. Run when you want to update your local collection.
    """
    templates = fetch_remote_templates()
    
    console.log(f"[green] {len(templates)} templates loaded remotely")
    jobs__templates()



@arguably.command
def jobs__run(template_name, *others, values_path=None):
    """
    Deploy and run a template job.

    Args:
        *others: all the other positional arguments go here
    """
    expose = True

    paths, available_templates = zip(*get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR)
    )
    
    if template_name not in available_templates:
        console.log(f"[red]{template_name} not found")
        jobs__templates()
        return
    
    path = paths[available_templates.index(template_name)]
    template_path = os.path.join(path, template_name, "template.yaml")

    
    if values_path is None or not Path(values_path).is_file():
        console.log(f"[red]Values file {values_path} was not found")
        return
    
    template_yaml = load_template(
        template_path=template_path,
        values_path=values_path)

    # deploy template with kube-watcher
    data = {
        "object": {
            "group": "leaderworkerset.x-k8s.io",
            "api_version": "v1",
            "namespace": "default",
            "plural": "leaderworkersets"
        },
        "body": template_yaml
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_custom_object",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        if len(result['failed']) > 0:
            console.log(f"[red]Error when deploying template\n\n{result['failed']}")
            return
        if len(result['successful']) > 0:
            console.log(f"[green]Template {template_path} successfully deployed!")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return
    
    # expose lws with nodeport template if required
    if expose:
        sidecar_template_yaml = load_template(
            template_path=SERVICE_TEMPLATE_FILE,
            values_path=values_path
        )
        try:
            result = request_to_server(
                method="post",
                endpoint="/v1/deploy_generic_model",
                data={"config": sidecar_template_yaml},
                server_creds=USER_LOCAL_SERVER_FILE
            )
            if len(result['failed']) > 0:
                console.log(f"[red]Error when deploying sidecar\n\n{result['failed']}")
            if len(result['successful']) > 0:
                console.log(f"[green]Sidecar {template_path} successfully deployed!")
        except Exception as e:
            console.log(f"[red]Error when connecting to kalavai service: {str(e)}")

@arguably.command
def jobs__defaults(template_name, *others):
    """
    Fetch default values.yaml for a template job
    """
    paths, available_templates = zip(*get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR)
    )
    
    if template_name not in available_templates:
        console.log(f"[red]{template_name} not found")
        jobs__templates()
        return
    
    path = paths[available_templates.index(template_name)]
    values_path = os.path.join(path, template_name, "values.yaml")

    with open(values_path, "r") as f:
        print("".join(f.readlines()))


@arguably.command
def jobs__describe(template_name, *others):
    """
    Fetch documentation for a template job
    """
    paths, available_templates = zip(*get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR)
    )
    
    if template_name not in available_templates:
        console.log(f"[red]{template_name} not found")
        jobs__templates()
        return
    
    path = paths[available_templates.index(template_name)]
    values_path = os.path.join(path, template_name, "README.md")

    with open(values_path, "r") as f:
        print("".join(f.readlines()))


@arguably.command
def jobs__delete(*others, name):
    """
    Delete job in the cluster
    """
    # deploy template with kube-watcher
    data = {
        "namespace": "default",
        "label": TEMPLATE_LABEL, # this ensures that both lws template and services are deleted
        "value": name
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/delete_labeled_resources",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        console.log(f"[green] Success. {result}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


@arguably.command
def jobs__list(*others):
    """
    List jobs in the cluster
    """
    if not CLUSTER.is_cluster_init() or not CLUSTER.is_agent_running():
        console.log("[red]Kalavai is not running or not installed on your machine")

    data = {
        "group": "leaderworkerset.x-k8s.io",
        "api_version": "v1",
        "plural": "leaderworkersets",
        "namespace": ""
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/get_objects_of_type",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        deployment_names = [d["metadata"]["name"] for d in result["items"]]

    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return
    
    if len(deployment_names) == 0:
        console.log("[green]No deployments found.")
        return
    
    columns = ["Deployment", "Status", "Workers", "Endpoint"]
    rows = []
    for deployment in deployment_names:
        try:
            # get status for deployment
            data = {
                "group": "leaderworkerset.x-k8s.io",
                "api_version": "v1",
                "plural": "leaderworkersets",
                "namespace": "default",
                "name": deployment
            }
            result = request_to_server(
                method="post",
                endpoint="/v1/get_status_for_object",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE
            )
            if len(result) > 0:
                last = result[-1]
                statuses = f"{last['type']}: {last['message']}"
            else:
                statuses = "Unknown"
            # get pod statuses
            data = {
                "namespace": "default",
                "label": "leaderworkerset.sigs.k8s.io/name",
                "value": deployment
            }
            result = request_to_server(
                method="post",
                endpoint="/v1/get_pods_status_for_label",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE
            )
            workers = defaultdict(int)
            for _, status in result.items():
                workers[status] += 1
            workers = "\n".join([f"{k}: {v}" for k, v in workers.items()])
            # get URL details
            data = {
                "label": TEMPLATE_LABEL,
                "value": deployment,
                "types": ["NodePort"]
            }
            result = request_to_server(
                method="post",
                endpoint="/v1/get_ports_for_services",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE
            )
            node_ports = [p["node_port"] for s in result.values() for p in s["ports"]]

            urls = [f"http://{load_server_ip(USER_LOCAL_SERVER_FILE)}:{node_port}" for node_port in node_ports]
            rows.append((deployment, statuses, workers, "\n".join(urls)))

        except Exception as e:
            console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
            return
        
        console.print(
            generate_table(columns=columns, rows=rows)
        )
        
    console.log("Get more information about a deployment with [yellow]kalavai jobs logs <name of deployment> [white](note it only works when the deployment is complete)")


@arguably.command
def jobs__logs(*others, name, stream_interval=0):
    """
    Get logs for a specific job
    """
    data = {
        "namespace": "default",
        "label": "leaderworkerset.sigs.k8s.io/name",
        "value": name
    }
    while True:
        try:
            result = request_to_server(
                method="post",
                endpoint="/v1/get_logs_for_label",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE
            )
            if stream_interval == 0:
                for pod, logs in result.items():
                    console.log(f"[yellow]Pod {pod}")
                    console.log(f"[green]{logs}")
                break
            else:
                os.system("clear")
                for pod, logs in result.items():
                    print(f"[yellow]Pod {pod}")
                    print(f"[green]{logs}")
                time.sleep(stream_interval)
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
            return
            


if __name__ == "__main__":
    user_path("", create_path=True)
    
    arguably.run()