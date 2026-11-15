#!/bin/bash
echo "$(date +%H:%M:%S) wall=$(date +%s) uptime=$(cut -d' ' -f1 /proc/uptime)"
