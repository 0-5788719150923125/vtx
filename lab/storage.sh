#!/bin/sh

journalctl --rotate

sudo journalctl --vacuum-time=2d
