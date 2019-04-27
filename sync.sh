#!/usr/bin/env bash

echo "DRY RUN"
rsync -n -avz --delete --chown=network-monitoring:network-monitoring \
  --exclude=venv/ --exclude=ap2mqtt.conf --exclude='.*' --exclude=__pycache__/ --exclude='*.pyc'  \
  . root@spacegate:/home/network-monitoring/ap2mqtt/

echo "Sync? Press any key to sync non dry..."
read x
rsync -avz --delete --chown=network-monitoring:network-monitoring \
  --exclude=venv/ --exclude=ap2mqtt.conf --exclude='.*' --exclude=__pycache__/ --exclude='*.pyc'  \
  . root@spacegate:/home/network-monitoring/ap2mqtt/

