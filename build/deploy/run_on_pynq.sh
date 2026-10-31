#!/bin/sh
# PYNQ 3.1.1: sudo drops the virtualenv PATH and XILINX_XRT.
set -eu
cd "$(dirname "$0")"
if [ -f herb_models.xsa ]; then
    echo 'Move herb_models.xsa into hardware_export/ before loading the .bit on PYNQ 3.1.1.' >&2
    exit 1
fi
exec sudo env XILINX_XRT=/usr BOARD=Pynq-Z2 /usr/local/share/pynq-venv/bin/python -u replay_models.py --directory .
