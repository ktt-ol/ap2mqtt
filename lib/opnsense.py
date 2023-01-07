import json
from typing import List

import requests

from lib.BaseClientInfoProvider import ClientInfo, BaseClientInfoProvider


class OPNsense(BaseClientInfoProvider):
    """
    https://docs.opnsense.org/development/how-tos/api.html#code-sample-python
    """

    def __init__(self, server, api_key, api_secret):
        self.api_secret = api_secret
        self.api_key = api_key
        self.rest_url = f"https://{server}/api/diagnostics/interface/getArp"

    def read_clients(self, retry_ok=True) -> List[ClientInfo]:
        r = requests.get(self.rest_url, verify=False, auth=(self.api_key, self.api_secret))

        if r.status_code != 200:
            raise Exception(f"Non 200 status code: {r.status_code}. Content: {r.text}")

        response = json.loads(r.text)
        devices: List[ClientInfo] = []
        for entry in response:
            mac = entry['mac']
            ip = entry['ip']
            print(f"{mac} -> {ip}")
            devices.append(ClientInfo(ip, [], mac, 0, ""))

        return devices
