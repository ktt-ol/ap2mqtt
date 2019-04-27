#!/usr/bin/env python3
import configparser

from wlancli import WLANControllerCLI
from datetime import datetime


def traffic(bytes):
    if bytes <= 1024:
        return "{} B".format(bytes)
    elif bytes <= 1024 * 1024:
        return "{} KiB".format(bytes / 1024)
    elif bytes <= 1024 * 1024 * 1024:
        return "{} MiB".format(bytes / 1024 / 1024)
    else:
        return "{} GiB".format(bytes / 1024 / 1024 / 1024)


def timedelta(delta):
    # maxlen = 11
    if delta.days < 0:
        return "(???)"
    elif delta.days >= 1000:
        return "(999+ days)"
    elif delta.days >= 2:
        return "({} days)".format(delta.days)
    elif delta.seconds > 3600 * 2:
        return "({} hrs)".format(delta.seconds / 3600)
    elif delta.seconds >= 60 * 2:
        return "({} mins)".format(delta.seconds / 60)
    elif delta.seconds >= 0:
        return "({} secs)".format(delta.seconds)


def byte2str(input):
    if type(input) is bytes:
        return input.decode('utf-8')

    return input


def dump(userinfo):
    print(
        "+-------------------+-----------------+---------------------------+-----+----------+---------------------------+-----+------+------+----------+----------+---------------------------------+---------------------------------+")
    print(
        "| MAC               | IP              | Hostname (DHCP)           | AP  | VLAN     | SSID                      | SNR | RSSI | Rate | CL -> AP | AP -> CL | Session Start                   | Last Activity                   |")
    print(
        "+-------------------+-----------------+---------------------------+-----+----------+---------------------------+-----+------+------+----------+----------+---------------------------------+---------------------------------+")

    for data in sorted(userinfo.values(), key=lambda x: (x["vlan"], x["ap"], x["radio"])):
        stats = data.get("stats", {})
        rx = traffic(stats.get("rx-unicast-bytes", 0) + stats.get("rx-multicast-bytes", 0))
        tx = traffic(stats.get("tx-unicast-bytes", 0))

        now = datetime.now()
        start = datetime.utcfromtimestamp(data["session-start"])
        last = datetime.utcfromtimestamp(data["last-activity"])

        startstr = start.strftime('%Y-%m-%d %H:%M:%S')
        laststr = last.strftime('%Y-%m-%d %H:%M:%S')
        startdiff = timedelta(now - start)
        lastdiff = timedelta(now - last)

        if data["last-activity"] == 0:
            laststr = "                   "
            lastdiff = ""

        # print now, "---", last, "----", now-last

        print(
            '| {} | {:>15} | {:>25.25} | {}/{} | {:>8} | {:>25.25} | {:>3} | {:>4} | {:>4} | {:>8.8} | {:>8.8} | {} {:>11.11} | {} {:>11.11} |'.format(
                byte2str(data["mac"]), byte2str(data["ip"]), byte2str(data["hostname"]), byte2str(data["ap"]),
                byte2str(data["radio"]), byte2str(data["vlan"]), byte2str(data["ssid"]), byte2str(data["last-snr"]), byte2str(data["last-rssi-dbm"]),
                byte2str(data["last-rate-mbits"]), byte2str(rx), byte2str(tx), byte2str(startstr), byte2str(startdiff), byte2str(laststr),
                byte2str(lastdiff)))
    print(
        "+-------------------+-----------------+---------------------------+-----+----------+---------------------------+-----+------+------+----------+----------+---------------------------------+---------------------------------+")


config = configparser.ConfigParser()
config.read("ap2mqtt.conf")
cliauth = config["cliauth"]
cli = WLANControllerCLI(cliauth["server"], cliauth["port"], cliauth["username"], cliauth["password"])
cli.cmd_user_sessions()
cli.exit()

dump(cli.userdata)
