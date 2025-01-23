import socket

from jinja2 import Template


template_str = """
services:
   kalavai:
      image: bundenth/kalavai-runner:gpu-latest
      hostname: {{hostname}}
      privileged: true
      network_mode: "host"
      command: >
        {{command}}
{% if command == "agent" %}
        --server {{pool_ip}}
        --token {{token}}
{% endif %}
        --node-label role={{command}}
        --node-label kalavai.storage.enabled={{storage_enabled}}
{% if num_gpus and num_gpus > 0 %}
        --node-label gpu=on
{% else %}
        --node-label gpu=off
{% endif %}
        --flannel-backend wireguard-native
        --node-ip {{ip_address}}
        --node-external-ip {{ip_address}}
{% if flannel_iface %}
        --flannel-iface {{flannel_iface}}
{% endif %}
      volumes:
      - /var/lib/kalavai/k3s:/var/lib/rancher/k3s # Persist data
      - /etc/kalavai/k3s:/etc/rancher/k3s # Config files
{% if num_gpus and num_gpus > 0 %}
      deploy:
        resources:
          reservations:
            devices:
            - driver: nvidia
              count: {{num_gpus}}
              capabilities: [gpu]
{% endif %}
        
"""

result = Template(template_str).render(
    {
        "hostname": socket.gethostname(),
        "command": "server",
        "pool_ip": "127.0.0.1",
        "token": "TOKEN",
        "storage_enabled": "True",
        "ip_address": "192.168.68.67",
        "num_gpus": 1,
        "flannel_iface": None
    }
)
print(result)