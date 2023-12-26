system.packages.update:
  pkg.uptodate:
    - refresh : True

system.packages.install:
  pkg.installed:
    - pkgs:
      - ca-certificates 
      - curl 
      - gcc
      - gnupg
      - vim
