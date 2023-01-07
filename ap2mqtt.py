#!/usr/bin/env python3
import configparser
import time

import sdnotify

from lib.opnsense import OPNsense
from lib.unifiWeb import UnifiWeb
from lib.wlanmqtt import WLANMQTT

config = configparser.ConfigParser()
config.read("ap2mqtt.conf")

cliauth = config["cliauth"]
# old_ctrl = OldControllerTelnet(cliauth["server"], cliauth["port"], cliauth["username"], cliauth["password"])
# ruckus_config = config["ruckus"]
## ruckus = RuckusTelnet(ruckus_config["server"], ruckus_config["port"], ruckus_config["username"], ruckus_config["password"])
# ruckus = RuckusWeb(ruckus_config["server"], ruckus_config["username"], ruckus_config["password"])
unifi_config = config["unifi"]
unifi = UnifiWeb(unifi_config["server"], unifi_config["username"], unifi_config["password"])

opnsense_config = config["opnsense"]
opnsense = OPNsense(opnsense_config["server"], opnsense_config["api_key"], opnsense_config["api_secret"])

mqtt = WLANMQTT([unifi, opnsense], config["mqttauth"])
while mqtt.connected is None:
    time.sleep(1)

systemdnotifier = sdnotify.SystemdNotifier()
systemdnotifier.notify("READY=1")

interval: int = int(config["global"]["interval"])
print(f"starting update loop (interval: {interval})...")
while mqtt.update():
    systemdnotifier.notify("WATCHDOG=1")
    time.sleep(interval)
