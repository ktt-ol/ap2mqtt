import warnings
from typing import List
import requests
import json
import time

from lib.BaseClientInfoProvider import BaseClientInfoProvider, ClientInfo


class UnifiWeb(BaseClientInfoProvider):
    """
    Gets wifi client information from the Ubiquiti wifi controller web interface.
    """

    def __init__(self, server, username, password):
        self.proxies = {}

        # build URLs for Ruckus web interface
        base_url = 'https://' + server + ':8443/api/'
        self.login_url = base_url + 'login'
        self.data_url = base_url + 's/default/stat/sta'
        self.credentials = {"username": username, "password": password}
        self.ap_mac_table = {
            "74:ac:b9:20:be:a0": 201, # Vorstandsbüro
            "74:ac:b9:20:e0:e4": 202, # Flur vorne
            "74:ac:b9:20:c9:51": 203, # E-Werkstatt
            "e0:63:da:53:2e:27": 205, # Lounge
            "74:ac:b9:20:c6:be": 206, # Flur hinten
            "74:ac:b9:20:c7:2c": 207, # Treppenhaus Schacht
            "80:2a:a8:46:65:0a": 208, # Holzwerkstatt Vorraum
            "80:2a:a8:46:69:d3": 209, # Holzwerkstatt Hauptraum
            "e0:63:da:b9:5f:d5": 210, # Lager
            "e0:63:da:b9:8e:76": 211, # Metallwerkstatt (alt)
            "80:2a:a8:46:64:2d": 211, # Metallwerkstatt (neu)
            "74:ac:b9:20:c6:67": 212, # Radstelle
            "80:2a:a8:46:65:28": 213, # Dach OG6
            "80:2a:a8:46:63:75": 214, # KG Lastenaufzug
        }

        # Use session handling
        self._session = None

        warnings.filterwarnings("ignore", "Unverified HTTPS request.")

    def _login(self):
        self._session = requests.Session()
        # Login to Ruckus web frontend and get session cookie
        credentials = json.dumps(self.credentials).encode('ascii')
        self._session.headers.update({'Content-Type': 'application/json'})
        r = self._session.post(self.login_url, verify=False, allow_redirects=False, proxies=self.proxies, data=credentials)
        # Verify that Login succeeded
        if r.status_code == 200 and json.loads(r.text).get("meta", {}).get("rc", "failed") == "ok":
            print(f"Unifi Login successful.")
        else:
            raise BaseException(f"Login to Ruckus server on {self.login_url} failed. http status: {r.status_code}. message: '{r.text}'")

    def read_clients(self, retry_ok=True) -> List[ClientInfo]:
        if self._session is None:
            self._login()

        r = self._session.post(self.data_url, verify=False, allow_redirects=False, proxies=self.proxies)
        data = json.loads(r.text)

        # Try to re-login on error
        if r.status_code != 200 and data.get("meta", {}).get("rc", "failed") != "ok":
            print(f"Session lost. Do login. (http {r.status_code})")
            if not retry_ok:
                raise BaseException("Missing session, already retried.")
            # new session and retry
            self._session = None
            return self.read_clients(retry_ok=False)

        devices: List[ClientInfo] = []
        now = int(time.time())

        for entry in data["data"]:
            if (entry["last_seen"] > now-300): # last 5min
                ap=self.ap_mac_table.get(entry["ap_mac"], 0)
                essid=entry.get("essid", "")
                devices.append(ClientInfo(ipv4=entry.get("ip", ""), ipv6=[], mac=entry.get("mac", ""), ap=int(ap), location=""))

        return devices

    def exit(self):
        # currently unused
        pass
