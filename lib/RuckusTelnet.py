import re
import telnetlib
from typing import List, Dict

from lib.BaseClientInfoProvider import BaseClientInfoProvider, ClientInfo

regex_4space_kv = re.compile(br"^\s{4}([^=]+)=(.+)$")
regex_6space_kv = re.compile(br"^\s{6}([^=]+)=(.+)$")

regex_ap_number = re.compile(br"^\s{4}\d+:$")


class ApInfo:
    def __init__(self, number: int, mac: str, location: str):
        self.number = number
        self.mac = mac
        self.location = location

    def __str__(self):
        return "%s, %s, %s" % (self.number, self.mac, self.location)


class RuckusTelnet(BaseClientInfoProvider):
    def __init__(self, hostname, port, username, password):
        self.data = {}
        self.userdata = {}
        self.tn = self._connect(hostname, port, username, password)
        self.ap_data: Dict[str, ApInfo] | None = None

    def _connect(self, hostname, port, username, password):
        tn = telnetlib.Telnet(hostname, port)
        tn.read_until(b"Please login: ")
        tn.write(bytes(username + "\r\n", 'utf-8'))
        tn.read_until(b"Password: ")
        tn.write(bytes(password + "\r\n", 'utf-8'))
        tn.read_until(b"ruckus> ")
        tn.write(b"enable\r\n")
        tn.read_until(b"ruckus# ", 5)
        return tn

    def _get_ap_data(self) -> Dict[str, ApInfo]:
        if self.ap_data is None:
            self.tn.write(bytes(b"show ap all\r\n"))
            response = self.tn.read_until(b"ruckus# ", 15)

            self.ap_data = {}
            ap_block: Dict[str, str] | None = None
            for line in response.split(b"\r\r\n"):

                if ap_block is not None:
                    if not line.startswith(b"      "):
                        # print(ap_block)
                        ap_mac = ap_block["MAC Address"].strip()
                        self.ap_data[ap_mac] = ApInfo(
                            to_int(ap_block["Description"].strip(), -1),
                            ap_mac,
                            ap_block["Location"].strip()
                        )
                        ap_block = None

                    if line.startswith(b"        "):
                        # ignored
                        continue

                    entry = regex_6space_kv.findall(line)
                    if entry:
                        ap_block[entry[0][0].decode("utf-8")] = entry[0][1].decode("utf-8")

                if regex_ap_number.findall(line):
                    ap_block = {}
                    continue

        return self.ap_data

    def read_clients(self) -> List[ClientInfo]:
        ap_map = self._get_ap_data()

        self.tn.write(bytes(b"show current-active-clients all\r\n"))
        response = self.tn.read_until(b"ruckus# ", 15)

        clients: List[ClientInfo] = []
        client_block = None
        for line in response.split(b"\r\r\n"):
            if client_block is not None:
                if not line.startswith(b'    '):
                    ap_mac = client_block["Access Point"].strip()
                    ap = ap_map.get(ap_mac)
                    clients.append(ClientInfo(
                        client_block["User/IP"].strip(),
                        [],
                        client_block["Mac Address"].strip(),
                        ap.number if ap is not None else -1,
                        ap.location if ap is not None else ""
                    ))
                    client_block = None
                else:
                    entry = regex_4space_kv.findall(line)
                    if entry:
                        client_block[entry[0][0].decode("utf-8")] = entry[0][1].decode("utf-8")
                        continue

            if line == b'  Clients:':
                client_block = {}
                continue

            if line == b'Last 300 Events/Activities:':
                break

        return clients

    def exit(self):
        self.tn.write(b"exit\r\n")
        self.tn.read_all()
        self.tn.close()


def to_int(s: str, fallback: int) -> int:
    try:
        return int(s)
    except ValueError:
        return fallback
