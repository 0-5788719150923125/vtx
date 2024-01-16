vtx.clone_repo:
  cmd.run:
    - name: >
        GIT_ASKPASS=/bin/true git clone --recurse-submodules https://github.com/0-5788719150923125/vtx.git /home/one/vtx --config credential.helper="" || true
    - unless: test -f vtx/README.md
    - runas: one

vtx.checkout_submodules:
  cmd.run:
    - name: >
        git submodule foreach 'git reset --hard && git checkout . && git clean -fdx' || true
    - unless: test -f vtx/src/aigen/README.md
    - runas: one
    - cwd: /home/one/vtx