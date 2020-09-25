from typing import List


class ClientInfo:
    def __init__(self, ipv4: str, ipv6: List[str], mac: str, ap: int, location: str):
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.mac = mac
        self.ap = ap
        self.location = location

    def __repr__(self):
        return f"{self.ipv4}, {self.ipv6}, {self.mac}, {self.ap}, {self.location}"