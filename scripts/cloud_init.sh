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

        # Create the required directory for Docker's keyrings
        install -m 0755 -d /etc/apt/keyrings

        # Add Docker’s official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc

        # Add the Docker repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"${UBUNTU_CODENAME:-$VERSION_CODENAME}\") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Update package lists and install Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        # Add the current user to the docker group
        groupadd docker || true
        usermod -aG docker ubuntu

        # Set up a Python virtual environment and install kalavai-client
        sudo -u ubuntu bash -c 'virtualenv -p python3 ~/kalavai'
        sudo -u ubuntu bash -c '~/kalavai/bin/pip install kalavai-client'
        sudo -u ubuntu bash -c 'kalavai auth {{user_id}}'
        sudo -u ubuntu bash -c 'kalavai pool start {{name}} --location {{vpn_key}} --non-interactive'

        # Mark first-boot complete
        touch /etc/first-boot-done
        sudo -u ubuntu bash -c 'shutdown -r now'
      fi

  - path: /etc/systemd/system/kalavai-startup.service
    permissions: '0644'
    content: |
      [Unit]
      Description=Start Kalavai GUI on boot
      After=network.target

      [Service]
      Type=simple
      User=ubuntu
      WorkingDirectory=/home/ubuntu
      ExecStart=/bin/bash -c "source /home/ubuntu/kalavai/bin/activate && kalavai gui start"
      Restart=always

      [Install]
      WantedBy=multi-user.target

runcmd:
  - bash /usr/local/bin/first-boot.sh  # Ensure first-boot tasks run once
  - systemctl daemon-reload
  - systemctl enable kalavai-startup.service
  - systemctl start kalavai-startup.service