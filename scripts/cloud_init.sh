#cloud-config
package_update: true
packages:
  - python3-virtualenv
  - ca-certificates
  - curl

write_files:
  - path: /usr/local/bin/first-boot.sh
    permissions: '0755'
    content: |
      #!/bin/bash
      if [ ! -f /etc/first-boot-done ]; then
        echo "Running first-boot setup..."

        # Install podamn
        sudo apt-get -y install podman
        

        # Set up a Python virtual environment and install kalavai-client
        # sudo -u ubuntu bash -c 'virtualenv -p python3 ~/kalavai'
        # sudo -u ubuntu bash -c 'source ~/kalavai/bin/activate && pip install kalavai-client'
        # sudo -u ubuntu bash -c 'source ~/kalavai/bin/activate && kalavai auth {{user_id}}'
        # sudo -u ubuntu bash -c 'source ~/kalavai/bin/activate && kalavai pool start {{name}} --location {{vpn_key}} --non-interactive'
        # sudo -u ubuntu bash -c 'source ~/kalavai/bin/activate && ACCESS_KEY={{user_id}} kalavai gui start'
        virtualenv -p python3 ~/kalavai
        source ~/kalavai/bin/activate && pip install kalavai-client
        source ~/kalavai/bin/activate && kalavai auth {{user_id}}
        source ~/kalavai/bin/activate && kalavai pool start {{name}} --location {{vpn_key}} --non-interactive
        source ~/kalavai/bin/activate && kalavai gui start
        
        # Mark first-boot complete
        touch /etc/first-boot-done
      fi

runcmd:
  - bash /usr/local/bin/first-boot.sh  # Ensure first-boot tasks run once