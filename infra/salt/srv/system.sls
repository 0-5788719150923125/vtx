system.packages.update:
  pkg.uptodate:
    - refresh : True

system.packages.install:
  pkg.installed:
    - pkgs:
      - ca-certificates 
      - curl 
      - gcc
      - git
      - gnupg
      - python3-venv
      - vim
