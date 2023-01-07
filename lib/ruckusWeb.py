import warnings
from typing import List
from xml.dom import minidom
import ssl

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

from lib import ClientInfo

class TLS1Adapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)

class RuckusWeb:
    """
    Gets wifi client information from the Ruckus wifi controller web interface.
    """

    # AJAX request string for currently active clients
    ajaxRequestString = '<ajax-request action="getstat" comp="stamgr"><client LEVEL="1"/><pieceStat start="0" pid="1" number="1000" requestId="clientsummary"/></ajax-request>'

    def __init__(self, server, username, password):
        # Proxy server for debugging purposes
        self.proxies = {}
        # self.proxies = {
        # 'http': 'http://127.0.0.1:8888',
        # 'https': 'http://127.0.0.1:8888',
        # }

        # build URLs for Ruckus web interface
        base_url = 'https://' + server + '/admin/'
        self.login_url = base_url + 'login.jsp'
        self.data_url = base_url + '_cmdstat.jsp'
        self.dashboard_url = base_url + 'dashboard.jsp'

        # http POST values for login page
        self.login_vals = {'username': username,
                           'password': password,
                           'ok': 'Log In'}

        # Use session handling
        self._session = None

        warnings.filterwarnings("ignore", "Unverified HTTPS request.")

    def _login(self):
        self._session = requests.Session()
        self._session.mount('https://', TLS1Adapter())
        # Login to Ruckus web frontend and get session cookie
        r = self._session.post(self.login_url, verify=False, allow_redirects=False, proxies=self.proxies, data=self.login_vals)
        # after a successful login we'll get redirected (302) to the dashboard
        if r.status_code == 302 and r.headers['Location'] == self.dashboard_url:
            print(f"Ruckus Login successful.")
        else:
            raise BaseException(f"Login to Ruckus server on {self.login_url} failed. http status: {r.status_code}. message: '{r.text}'")

    def read_clients(self, retry_ok=True) -> List[ClientInfo]:
        if self._session is None:
            self._login()

        # Get currently active clients (XML)
        r = self._session.post(self.data_url, verify=False, allow_redirects=False, proxies=self.proxies, data=self.ajaxRequestString)
        # if the session is missing/invalid we'll get redirected (302) to the login
        if r.status_code == 302 and r.headers["Location"] == self.login_url:
            print(f"Session lost. Do login. (http {r.status_code})")
            if not retry_ok:
                raise BaseException("Missing session, already retried.")
            # new session and retry
            self._session = None
            self.read_clients(retry_ok=False)

        # Parse XML
        xmlDoc = minidom.parseString(r.text)
        itemlist = xmlDoc.getElementsByTagName('client')

        # Parse XML to internal data structure
        devices: List[ClientInfo] = []
        for s in itemlist:
            entry = {}
            for k, v in s.attributes.items():
                entry[k] = v
            ipv6_list = []
            if entry["ipv6"] != "":
                ipv6_list.append(entry["ipv6"])
            devices.append(ClientInfo(ipv4=entry["ip"], ipv6=ipv6_list, mac=entry["mac"], ap=int(entry["description"]), location=entry["location"]))

        return devices

    def exit(self):
        # currently unused
        pass
