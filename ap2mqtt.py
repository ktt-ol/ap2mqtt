#!/usr/bin/env python3
import configparser

from lib.RuckusTelnet import RuckusTelnet
from lib.wlanmqtt import WLANMQTT
from lib.oldCtrlTelnet import OldControllerTelnet
import time
import sdnotify

config = configparser.ConfigParser()
config.read("ap2mqtt.conf")

cliauth = config["cliauth"]
old_ctrl = OldControllerTelnet(cliauth["server"], cliauth["port"], cliauth["username"], cliauth["password"])
ruckus_config = config["ruckus"]
ruckus = RuckusTelnet(ruckus_config["server"], ruckus_config["port"], ruckus_config["username"], ruckus_config["password"])

mqtt = WLANMQTT(old_ctrl, ruckus, config["mqttauth"])
while mqtt.connected is None:
    time.sleep(1)

systemdnotifier = sdnotify.SystemdNotifier()
systemdnotifier.notify("READY=1")

interval: int = int(config["global"]["interval"])
print(f"starting update loop (interval: {interval})...")
while mqtt.update():
    systemdnotifier.notify("WATCHDOG=1")
    time.sleep(interval)
