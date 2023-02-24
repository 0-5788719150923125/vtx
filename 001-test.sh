#!/bin/sh

# apt-get update -y

# apt-get install -y fuse

uname -r

ipfs config --json Mounts.FuseAllowOther true
