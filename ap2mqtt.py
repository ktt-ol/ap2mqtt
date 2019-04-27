#!/usr/bin/env python3
import configparser

from wlanmqtt import WLANMQTT
from wlancli import WLANControllerCLI
import time
import sdnotify

config = configparser.ConfigParser()
config.read("ap2mqtt.conf")

mqttauth = config["mqttauth"]
cliauth = config["cliauth"]

systemdnotifier = sdnotify.SystemdNotifier()
cli = WLANControllerCLI(cliauth["server"], cliauth["port"], cliauth["username"], cliauth["password"])
mqtt = WLANMQTT(cli, mqttauth)
while mqtt.connected is None:
    time.sleep(1)

systemdnotifier.notify("READY=1")

print("starting update loop...")
while mqtt.update():
    systemdnotifier.notify("WATCHDOG=1")
    time.sleep(10)
