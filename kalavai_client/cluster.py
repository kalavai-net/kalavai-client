import os
from pathlib import Path
from abc import ABC, abstractmethod

from kalavai_client.utils import (
    run_cmd,
    user_path,
    check_gpu_drivers
)


class Cluster(ABC):
    @abstractmethod
    def start_seed_node(self, ip_address, cluster_config_file, labels):
        raise NotImplementedError()

    @abstractmethod
    def start_worker_node(self, url, token, node_name, auth_key, watcher_service, ip_address, labels):
        raise NotImplementedError()


    @abstractmethod
    def install_dependencies(self, dependencies_file, kubeconfig_file):
        run_cmd(f"helmfile sync --file {dependencies_file} --kubeconfig {kubeconfig_file} >/dev/null 2>&1")


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
    

class k0sCluster(Cluster):

    def __init__(self, kubeconfig_file, kube_version="v1.31.1+k3s1", flannel_iface=None):
        self.kube_version = kube_version
        self.flannel_iface = flannel_iface
        self.kubeconfig_file = kubeconfig_file


    def start_seed_node(self, ip_address, cluster_config_file, labels):
        run_cmd("curl -sSLf https://get.k0s.sh | sudo sh")
        run_cmd("helm repo update")

        run_cmd(f"sudo k0s install controller -c {cluster_config_file} --enable-worker --no-taints")
        run_cmd("sudo k0s start")

        run_cmd(f"sudo cp /var/lib/k0s/pki/admin.conf {self.kubeconfig_file}")
        run_cmd(f"sudo chown $USER {self.kubeconfig_file}")


    def start_worker_node(self, url, token, node_name, ip_address, labels):
        temp_file = user_path(".token")
        with open(temp_file, "w") as f:
            f.write(token)
        run_cmd("curl -sSLf https://get.k0s.sh | sudo sh")
        run_cmd(f"sudo k0s install worker --token-file {temp_file}")
        run_cmd("sudo k0s start")


    def install_dependencies(self, dependencies_file):
        super().install_dependencies(
            dependencies_file=dependencies_file,
            kubeconfig_file=self.kubeconfig_file)


    def remove_agent(self):
        # send request to remove node on watcher
        run_cmd("sudo k0s stop")
        run_cmd("sudo k0s reset")

    def is_agent_running(self):
        status = 0 == os.system("sudo k0s status >/dev/null 2>&1")
        return status

    def is_seed_node(self):
        return 0 == os.system("sudo k0s kubectl get nodes >/dev/null 2>&1")

    def is_cluster_init(self):
        return 0 == os.system("command -v k0s >/dev/null 2>&1")

    def pause_agent(self):
        try:
            run_cmd("sudo k0s stop")
            return True
        except:
            return False

    def restart_agent(self):
        try:
            run_cmd("sudo k0s start")
            return True
        except:
            return False

    def get_cluster_token(self):
        return run_cmd("sudo k0s token create --role=worker").decode("utf-8")
    
    def diagnostics(self) -> str:
        data = run_cmd("sudo k0s kubectl get pods -A -o wide").decode() + "\n\n" + run_cmd("sudo k0s kubectl get nodes").decode()
        return data


class k3sCluster(Cluster):

    def __init__(self, kubeconfig_file, kube_version="v1.31.1+k3s1", flannel_iface=None):
        self.kube_version = kube_version
        self.kubeconfig_file = kubeconfig_file

        if flannel_iface is not None:
            self.flannel_iface = f"--flannel-iface {flannel_iface}"
        else:
            self.flannel_iface = ""
        try:
            if check_gpu_drivers():
                self.node_labels = "--node-label gpu=on"
        except:
            print("[Warning] issues detected with nvidia, GPU has been disabled for this node")
            self.node_labels = ""
        
    def start_seed_node(self, ip_address, cluster_config_file, labels=None):
        node_labels = self.node_labels 
        if labels is not None:
            for key, value in labels.items():
                node_labels += f" --node-label {key}={value}"

        run_cmd(f'curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="{self.kube_version}" INSTALL_K3S_EXEC="server --node-ip {ip_address} --node-external-ip {ip_address} {self.flannel_iface} --flannel-backend wireguard-native {node_labels}" sh - >/dev/null 2>&1')
        run_cmd(f"sudo cp /etc/rancher/k3s/k3s.yaml {self.kubeconfig_file}")
        run_cmd(f"sudo chown $USER {self.kubeconfig_file}")


    def start_worker_node(self, url, token, node_name, ip_address, labels=None):
        node_labels = self.node_labels 
        if labels is not None:
            for key, value in labels.items():
                node_labels += f" --node-label {key}={value}"
        command = f'curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="{self.kube_version}" INSTALL_K3S_EXEC="agent --token {token} --server {url} --node-name {node_name} --node-ip {ip_address} --node-external-ip {ip_address} {self.flannel_iface} {node_labels}" sh - >/dev/null 2>&1'
        run_cmd(command)
        

    def install_dependencies(self, dependencies_file):
        super().install_dependencies(
            dependencies_file=dependencies_file,
            kubeconfig_file=self.kubeconfig_file)


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
        try:
            run_cmd('sudo systemctl stop k3s >/dev/null 2>&1')
        except:
            pass
        try:
            run_cmd('sudo systemctl stop k3s-agent >/dev/null 2>&1')
        except:
            pass


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
