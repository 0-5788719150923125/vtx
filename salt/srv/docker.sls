docker.keyring:
  cmd.run:
    - name: >
        install -m 0755 -d /etc/apt/keyrings &
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg &
        chmod a+r /etc/apt/keyrings/docker.gpg &
        echo \
            "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
            $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
            tee /etc/apt/sources.list.d/docker.list > /dev/null

docker.packages.update:
  pkg.uptodate:
    - refresh : True

docker.packages.install:
  pkg.installed:
    - pkgs:
      - docker-ce 
      - docker-ce-cli 
      - containerd.io 
      - docker-buildx-plugin 
      - docker-compose-plugin

docker:
  group.present:
    - addusers:
      - one