import os
import time
from pathlib import Path
from abc import ABC, abstractmethod

from kalavai_client.utils import (
    run_cmd,
    check_gpu_drivers,
    validate_poolconfig,
    populate_template
)

from kalavai_client.env import (
    DEFAULT_CONTAINER_NAME,
    KUBE_VERSION,
    DEFAULT_FLANNEL_IFACE,
    USER_COMPOSE_FILE,
    USER_KUBECONFIG_FILE,
    USER_LOCAL_SERVER_FILE,
    USER_HELM_APPS_FILE,
    user_path
)


class Cluster(ABC):
    @abstractmethod
    def start_seed_node(self, ip_address, labels, flannel_iface):
        raise NotImplementedError()

    @abstractmethod
    def start_worker_node(self, url, token, node_name, auth_key, watcher_service, ip_address, labels, flannel_iface):
        raise NotImplementedError()

    @abstractmethod
    def get_vpn_ip(self):
        raise NotImplementedError()

    @abstractmethod
    def update_dependencies(self, dependencies_files):
        raise NotImplementedError()


    @abstractmethod
    def remove_agent(self):
        raise NotImplementedError()

    @abstractmethod
    def is_agent_running(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def is_seed_node(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def is_cluster_init(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def pause_agent(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def restart_agent(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_cluster_token(self) -> str:
        raise NotImplementedError()
    
    @abstractmethod
    def diagnostics(self) -> str:
        raise NotImplementedError()
    
    @abstractmethod
    def validate_cluster(self) -> bool:
        raise NotImplementedError
    
class dockerCluster(Cluster):
    def __init__(self, container_name, compose_file, kubeconfig_file, poolconfig_file, dependencies_file, kube_version="v1.31.1+k3s1", flannel_iface=None):
        self.kube_version = kube_version
        self.container_name = container_name
        self.compose_file = compose_file
        self.kubeconfig_file = kubeconfig_file
        self.poolconfig_file = poolconfig_file
        self.dependencies_file = dependencies_file

        if flannel_iface is not None:
            self.default_flannel_iface = flannel_iface
        else:
            self.default_flannel_iface = ""
        
    def start_seed_node(self):
        
        run_cmd(f"docker compose -f {self.compose_file} up -d")
        # wait for container to be setup
        while True:
            try:
                run_cmd(f"docker cp {self.container_name}:/etc/rancher/k3s/k3s.yaml {self.kubeconfig_file} >/dev/null 2>&1")
                break
            except:
                pass
            time.sleep(5)

    def start_worker_node(self):
        run_cmd(f"docker compose -f {self.compose_file} up -d")
    
    def get_vpn_ip(self):
        command = populate_template(
            template_str="docker exec -it {{container_name}} ifconfig {{iface_name}} | grep 'inet ' | awk '{gsub(/^addr:/, \"\", $2); print $2}'",
            values_dict={"container_name": self.container_name, "iface_name": self.default_flannel_iface})
        return run_cmd(command).decode().strip()
        

    def update_dependencies(self, dependencies_file=None, debug=False, retries=3):
        if dependencies_file is not None:
            self.dependencies_file = dependencies_file
        if debug:
            output = ""
        else:
            output = " >/dev/null 2>&1"
        while True:
            try:
                home = user_path("")
                run_cmd(f"docker run --rm --net=host -v {home}:{home} ghcr.io/helmfile/helmfile:v0.169.2 helmfile sync --file {self.dependencies_file} --kubeconfig {self.kubeconfig_file} {output}")
                #run_cmd(f"helmfile sync --file {self.dependencies_file} --kubeconfig {self.kubeconfig_file} {output}")
                break
            except Exception as e:
                if retries > 0:
                    retries -= 1
                    print(f"[{retries}] Dependencies failed. Retrying...")
                else:
                    raise Exception(f"Dependencies failed. Are you connected to the internet?\n\nTrace: {str(e)}")

    def remove_agent(self):
        try:
            run_cmd(f'docker compose -f {self.compose_file} down --volumes')
            return True
        except:
            return False

    def is_agent_running(self):
        if not os.path.isfile(self.compose_file):
            return False
        status = self.container_name in run_cmd(f"docker compose -f {self.compose_file} ps --services --status=running").decode()
        if not status:
            return False
        status = (0 == os.system(f'docker exec {self.container_name} ps aux | grep -v grep | grep -E "k3s (server|agent)"'))
        return status

    def is_seed_node(self):
        if not os.path.isfile(self.compose_file):
            return False
        if not self.is_agent_running():
            return False
        try:
            run_cmd(f"docker container exec {self.container_name} cat /var/lib/rancher/k3s/server/node-token >/dev/null 2>&1")
            return True
        except:
            return False
    
    def is_cluster_init(self):
        if not os.path.isfile(self.compose_file):
            return False
        status = self.container_name in run_cmd(f"docker compose -f {self.compose_file} ps --services --all").decode()
        return status

    def pause_agent(self):
        status = False
        try:
            run_cmd(f'docker compose -f {self.compose_file} stop')
            status = True
        except:
            pass
        return status

    def restart_agent(self):
        try:
            run_cmd(f'docker compose -f {self.compose_file} start')

        except:
            pass
        time.sleep(5)
        return self.is_agent_running()

    def get_cluster_token(self):
        if self.is_seed_node():
            return run_cmd(f"docker container exec {self.container_name} cat /var/lib/rancher/k3s/server/node-token").decode()
            #return run_cmd("sudo k3s token create --kubeconfig /etc/rancher/k3s/k3s.yaml --ttl 0").decode()
        else:
            return None
    
    def diagnostics(self) -> str:
        # TODO: check cache files are in order
        # get cluster status
        if self.is_seed_node():
            return run_cmd(f"docker exec {self.container_name} kubectl get pods -A -o wide").decode() + "\n\n" + run_cmd(f"docker exec {self.container_name} kubectl get nodes").decode()
        else:
            return None
        
    def validate_cluster(self) -> bool:
        # check if credentials are present
        return os.path.isfile(self.poolconfig_file)


class k3sCluster(Cluster):

    def __init__(self, kubeconfig_file, poolconfig_file, dependencies_file, kube_version="v1.31.1+k3s1", flannel_iface=None):
        self.kube_version = kube_version
        self.kubeconfig_file = kubeconfig_file
        self.poolconfig_file = poolconfig_file
        self.dependencies_file = dependencies_file

        if flannel_iface is not None:
            self.default_flannel_iface = flannel_iface
        else:
            self.default_flannel_iface = ""
        try:
            if check_gpu_drivers():
                self.node_labels = "--node-label gpu=on"
        except:
            print("[Warning] issues detected with nvidia, GPU has been disabled for this node")
            self.node_labels = ""
        
    def start_seed_node(self, ip_address, labels=None, is_public=False):
        node_labels = self.node_labels 
        if labels is not None:
            for key, value in labels.items():
                node_labels += f" --node-label {key}={value}"
        if is_public:
            flannel_iface = f"--flannel-iface {self.default_flannel_iface}"
        else:
            flannel_iface = ""
        run_cmd(f'curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="{self.kube_version}" INSTALL_K3S_EXEC="server --node-ip {ip_address} --node-external-ip {ip_address} {flannel_iface} --flannel-backend wireguard-native {node_labels}" sh - >/dev/null 2>&1')
        run_cmd(f"sudo cp /etc/rancher/k3s/k3s.yaml {self.kubeconfig_file}")
        run_cmd(f"sudo chown $USER {self.kubeconfig_file}")


    def start_worker_node(self, url, token, node_name, ip_address, labels=None, is_public=False):
        node_labels = self.node_labels 
        if labels is not None:
            for key, value in labels.items():
                node_labels += f" --node-label {key}={value}"
        if is_public:
            flannel_iface = f"--flannel-iface {self.default_flannel_iface}"
        else:
            flannel_iface = ""
        command = f'curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="{self.kube_version}" INSTALL_K3S_EXEC="agent --token {token} --server https://{url}:6443 --node-name {node_name} --node-ip {ip_address} --node-external-ip {ip_address} {flannel_iface} {node_labels}" sh - >/dev/null 2>&1'
        run_cmd(command)
        

    def update_dependencies(self, dependencies_file=None, debug=False, retries=3):
        if dependencies_file is not None:
            self.dependencies_file = dependencies_file
        if debug:
            output = ""
        else:
            output = " >/dev/null 2>&1"
        while True:
            try:
                run_cmd(f"helmfile sync --file {self.dependencies_file} --kubeconfig {self.kubeconfig_file} {output}")
                break
            except Exception as e:
                if retries > 0:
                    retries -= 1
                    print(f"[{retries}] Dependencies failed. Retrying...")
                else:
                    raise Exception(f"Dependencies failed. Are you connected to the internet?\n\nTrace: {str(e)}")
                

    def remove_agent(self):
        try:
            run_cmd('/usr/local/bin/k3s-uninstall.sh >/dev/null 2>&1')
            run_cmd('sudo rm -r /etc/rancher/node/ >/dev/null 2>&1')
            return True
        except:
            pass
        try:
            run_cmd('/usr/local/bin/k3s-agent-uninstall.sh >/dev/null 2>&1')
            return True
        except:
            pass
        return False

    def is_agent_running(self):
        status = (0 == os.system('sudo systemctl is-active --quiet k3s-agent.service')) or (0 == os.system('sudo systemctl is-active --quiet k3s.service'))
        return status

    def is_seed_node(self):
        return 0 == os.system('sudo systemctl is-active --quiet k3s.service')

    def is_cluster_init(self):
        status = Path("/usr/local/bin/k3s-agent-uninstall.sh").is_file() or Path("/usr/local/bin/k3s-uninstall.sh").is_file()
        return status

    def pause_agent(self):
        status = False
        try:
            run_cmd('sudo systemctl stop k3s >/dev/null 2>&1')
            status = True
        except:
            pass
        try:
            run_cmd('sudo systemctl stop k3s-agent >/dev/null 2>&1')
            status = True
        except:
            pass
        return status

    def restart_agent(self):
        try:
            run_cmd('sudo systemctl start k3s >/dev/null 2>&1')
        except:
            pass
        try:
            run_cmd('sudo systemctl start k3s-agent >/dev/null 2>&1')
        except:
            pass
        return self.is_agent_running()

    def get_cluster_token(self):
        if self.is_seed_node():
            return run_cmd("sudo cat /var/lib/rancher/k3s/server/node-token").decode()
            #return run_cmd("sudo k3s token create --kubeconfig /etc/rancher/k3s/k3s.yaml --ttl 0").decode()
        else:
            return None
    
    def diagnostics(self) -> str:
        if self.is_seed_node():
            return run_cmd(f"k3s kubectl get pods -A -o wide --kubeconfig {self.kubeconfig_file}").decode() + "\n\n" + run_cmd(f"k3s kubectl get nodes --kubeconfig {self.kubeconfig_file}").decode()
        else:
            return None
        
    def validate_cluster(self) -> bool:
        if not self.is_cluster_init():
            raise ValueError("Pool not initialised")
        if not self.is_agent_running():
            raise ValueError("Pool initialised but agent is not running")
        # check cache files
        if self.is_seed_node():
            if not validate_poolconfig(self.poolconfig_file):
                raise ValueError("Cache missconfigured. Run 'kalavai pool stop' to clear.")
        return True

####################################################
####################################################

CLUSTER = dockerCluster(
    container_name=DEFAULT_CONTAINER_NAME,
    kube_version=KUBE_VERSION,
    flannel_iface=DEFAULT_FLANNEL_IFACE,
    compose_file=USER_COMPOSE_FILE,
    kubeconfig_file=USER_KUBECONFIG_FILE,
    poolconfig_file=USER_LOCAL_SERVER_FILE,
    dependencies_file=USER_HELM_APPS_FILE
)