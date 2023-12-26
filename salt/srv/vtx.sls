'GIT_ASKPASS=/bin/true git clone --recurse-submodules https://github.com/0-5788719150923125/vtx.git /home/one/vtx --config credential.helper="" || true':
  cmd.run:
    - unless: test -f vtx/README.md

"git submodule foreach 'git reset --hard && git checkout . && git clean -fdx'"
  cmd.run