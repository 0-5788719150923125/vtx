'git clone --recurse-submodules https://github.com/0-5788719150923125/vtx.git':
  cmd.run:
    - unless: test -f vtx/README.md