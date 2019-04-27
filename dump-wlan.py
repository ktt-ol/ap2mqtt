#!/usr/bin/env python3
import configparser

from wlancli import WLANControllerCLI


def dumpAP(apinfo):
    for ap, data in apinfo.items():
        print(ap, data)


config = configparser.ConfigParser()
config.read("ap2mqtt.conf")
cliauth = config["cliauth"]
cli = WLANControllerCLI(cliauth["server"], cliauth["port"], cliauth["username"], cliauth["password"])
cli.cmd_ap_config()
cli.cmd_ap_status()
cli.cmd_ap_counters()
cli.exit()

dumpAP(cli.data)
