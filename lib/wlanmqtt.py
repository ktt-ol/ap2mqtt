import concurrent.futures
import json
import random
import ssl
import string
from typing import List
import sys

import paho.mqtt.client as mqtt

from lib.BaseClientInfoProvider import ClientInfo, BaseClientInfoProvider

# useful for testing, default should be True
RETAIN = True


class WLANMQTT:
    def __init__(self, client_provider: List[BaseClientInfoProvider], mqttauth):
        self.basepath = mqttauth["basepath"]
        self.sessionpath = mqttauth["session-path"]
        client_id = "%s-%s" % (
            mqttauth["clientid"],
            ''.join(random.choice(string.ascii_letters) for i in range(4))
        )
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        # ignore any ssl errors
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.tls_insecure_set(True)
        self.client.username_pw_set(mqttauth["username"], mqttauth["password"])
        self.client.connect(mqttauth["server"], int(mqttauth["port"]), 60)
        self.client.loop_start()

        self.connected = None

        self.cached = {}
        # self.old_ctrl = old_ctrl
        # self.ruckus = ruckus
        self.client_provider = client_provider

    def __exit__(self):
        for provider in self.client_provider:
            provider.exit()
        self.client.loop_stop()

    def update(self):
        if not self.connected:
            return False

        # data = self.cli.cmd_all()
        # for ap, apdata in data.items():
        #     self.__mqtt_publish_ap(ap, apdata)
        # self.cached = data

        self.__update_user_sessions()

        return True

    def __update_user_sessions(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_ci = []
            for provider in self.client_provider:
                future_to_ci.append(executor.submit(provider.read_clients))

            clients: List[ClientInfo] = []
            for future in concurrent.futures.as_completed(future_to_ci):
                clients += future.result()

            clients = WLANMQTT.merge_clients_list(clients)

            result = self.client.publish(self.sessionpath, json.dumps(clients, default=lambda x: x.__dict__), retain=RETAIN)
            result.wait_for_publish()

    @staticmethod
    def merge_clients_list(clients: List[ClientInfo]) -> List[ClientInfo]:
        by_mac: dict[str, ClientInfo] = {}

        for client in clients:
            if client.mac in by_mac:
                # merge values
                target = by_mac[client.mac]
                if client.ap > 0:
                    target.ap = client.ap
                if len(client.ipv6) > 0:
                    target.ipv6 = list(set(target.ipv6 + client.ipv6))
            else:
                # new entry
                by_mac[client.mac] = client

        return list(by_mac.values())

    def __mqtt_publish_ap(self, ap, data):
        apbase = self.basepath + "/ap-%02d/" % ap

        if self.cached.get(ap, {}).get("name", "") != data.get("name", ""):
            self.client.publish(apbase + "name", data.get("name", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get("model", "") != data.get("model", ""):
            self.client.publish(apbase + "model", data.get("model", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get("state", "") != data.get("state", ""):
            self.client.publish(apbase + "state", data.get("state", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get("ip", "") != data.get("ip", ""):
            self.client.publish(apbase + "ip", data.get("ip", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get("mac", "") != data.get("mac", ""):
            self.client.publish(apbase + "mac", data.get("mac", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get("uptime", 0) != data.get("uptime", 0):
            self.client.publish(apbase + "uptime", str(data.get("uptime", 0)))

        if 1 in data:
            self.__mqtt_publish_radio(ap, 1, data[1])

        if 2 in data:
            self.__mqtt_publish_radio(ap, 2, data[2])

    def __mqtt_publish_radio(self, ap, radio, data):
        radiobase = self.basepath + "/ap-%02d/radio-%d/" % (ap, radio)

        if self.cached.get(ap, {}).get(radio, {}).get("profile", "") != data.get("profile", ""):
            self.client.publish(radiobase + "profile", data.get("profile", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get(radio, {}).get("channel", "") != data.get("channel", ""):
            self.client.publish(radiobase + "channel", data.get("channel", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get(radio, {}).get("tx-power", "") != data.get("tx-power", ""):
            self.client.publish(radiobase + "tx-power", data.get("tx-power", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get(radio, {}).get("failed-associations", "") != data.get("failed-associations", ""):
            self.client.publish(radiobase + "failed-associations", data.get("failed-associations", ""))

        if self.cached.get(ap, {}).get(radio, {}).get("retransmitted-bytes", "") != data.get("retransmitted-bytes", ""):
            self.client.publish(radiobase + "retransmitted-bytes", data.get("retransmitted-bytes", ""))

        if self.cached.get(ap, {}).get(radio, {}).get("clients", "") != data.get("clients", ""):
            self.client.publish(radiobase + "clients", data.get("clients", ""))

        if self.cached.get(ap, {}).get(radio, {}).get("clients-in-power-save-mode", "") != data.get("clients-in-power-save-mode", ""):
            self.client.publish(radiobase + "clients-in-power-save-mode", data.get("clients-in-power-save-mode", ""))

        if self.cached.get(ap, {}).get(radio, {}).get("noise-floor", "") != data.get("noise-floor", ""):
            self.client.publish(radiobase + "noise-floor", data.get("noise-floor", ""))

        if self.cached.get(ap, {}).get(radio, {}).get("reset-counter", "") != data.get("reset-counter", ""):
            self.client.publish(radiobase + "reset-counter", data.get("reset-counter", ""), retain=RETAIN)

        if self.cached.get(ap, {}).get(radio, {}).get("state", "") != data.get("state", ""):
            self.client.publish(radiobase + "state", data.get("state", ""), retain=RETAIN)

        for speed, radiostats in data.get("stats", {}).items():
            self.__mqtt_publish_radio_stats(ap, radio, byte2str(speed), radiostats)

    def __mqtt_publish_radio_stats(self, ap, radio, speed, data):
        statsbase = self.basepath + "/ap-%02d/radio-%d/stats-%s/" % (ap, radio, speed)
        cachedstats = self.cached.get(ap, {}).get(radio, {}).get("stats", {}).get(speed, {})

        if cachedstats.get("tx-multicast-bytes", 0) != data.get("tx-multicast-bytes", 0):
            self.client.publish(statsbase + "tx-multicast-bytes", str(data.get("tx-multicast-bytes", 0)))

        if cachedstats.get("tx-multicast-pkts", 0) != data.get("tx-multicast-pkts", 0):
            self.client.publish(statsbase + "tx-multicast-pkts", str(data.get("tx-multicast-pkts", 0)))

        if cachedstats.get("tx-unicast-bytes", 0) != data.get("tx-unicast-bytes", 0):
            self.client.publish(statsbase + "tx-unicast-bytes", str(data.get("tx-unicast-bytes", 0)))

        if cachedstats.get("tx-unicast-pkts", 0) != data.get("tx-unicast-pkts", 0):
            self.client.publish(statsbase + "tx-unicast-pkts", str(data.get("tx-unicast-pkts", 0)))

        if cachedstats.get("rx-bytes", 0) != data.get("rx-bytes", 0):
            self.client.publish(statsbase + "rx-bytes", str(data.get("rx-bytes", 0)))

        if cachedstats.get("rx-pkts", 0) != data.get("rx-pkts", 0):
            self.client.publish(statsbase + "rx-pkts", str(data.get("rx-pkts", 0)))

        if cachedstats.get("phy-error", 0) != data.get("phy-error", 0):
            self.client.publish(statsbase + "phy-error", str(data.get("phy-error", 0)))

    def on_connect(self, client, userdata, flags, rc):
        self.connected = True
        if rc != 0:
            print("Connected with result code " + str(rc))

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("MQTT disconnected with code " + str(rc))
        # TODO: try to do a reconnect?
        sys.exit(1)


def byte2str(input):
    if type(input) is bytes:
        return input.decode('utf-8')

    return input
