nvidia-driver-535:
  pkg.installed

cuda.keyring:
  cmd.run:
    - name: >
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

cuda.packages.update:
  pkg.uptodate:
    - refresh : True

nvidia-container-toolkit:
  pkg.installed

# '> /var/log/messages/':
#   cmd.run:
#     - unless: echo 'foo' > /tmp/.test && rm -f /tmp/.test