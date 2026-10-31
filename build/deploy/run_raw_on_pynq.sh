#!/bin/sh
set -eu
cd "$(dirname "$0")"
exec sudo env XILINX_XRT=/usr BOARD=Pynq-Z2 /usr/local/share/pynq-venv/bin/python -u raw_event_replay.py "$@"
