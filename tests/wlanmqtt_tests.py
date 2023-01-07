import unittest
from typing import List

from lib.BaseClientInfoProvider import ClientInfo
from lib.wlanmqtt import WLANMQTT


class Tests(unittest.TestCase):

    def test_merge_clients_list(self):
        ci: List[ClientInfo] = [
            ClientInfo("100.100.100.100", [], "aa:aa:aa:aa:aa:aa", 0, ""),
            ClientInfo("100.100.100.101", [], "aa:aa:aa:aa:aa:ab", 0, ""),
            ClientInfo("", [], "aa:aa:aa:aa:aa:ab", 11, ""),
            ClientInfo("100.100.100.102", [], "aa:aa:aa:aa:aa:ac", 0, ""),
            ClientInfo("100.100.100.100", [], "aa:aa:aa:aa:aa:aa", 23, ""),
            ClientInfo("100.100.100.103", ["ip6a"], "aa:aa:aa:aa:aa:dd", 0, ""),
            ClientInfo("100.100.100.103", ["ip6b"], "aa:aa:aa:aa:aa:dd", 0, ""),
        ]

        result = WLANMQTT.merge_clients_list(ci)

        assert len(ci) == 7, "wrong test data"
        assert len(result) == 4

        print(result)

if __name__ == '__main__':
    unittest.main()
