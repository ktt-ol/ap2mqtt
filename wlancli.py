import calendar
import re
import telnetlib

from dateutil import parser as dateparser

regex_more = re.compile(br"^press any key to continue, q to quit.")
regex_prompt = re.compile(br"^Mainframe-WLAN-backup# ")

regex_ap_config = re.compile(br"([ 0-9]{4}) (.{16}) (.{10}) (.{8}) (.{16}) (.{16})\r\n")
regex_ap_status = re.compile(br"([ 0-9]{4}) (.{4}) (.{15}) (.{12}) (.{17}) (.{7}) (.{7}) (.{6})\r\n")

regex_ap_counters1 = re.compile(br"^AP: (\d+)[ ]+radio: (\d+)[ ]*$")
regex_ap_counters2 = re.compile(br"^([A-Za-z0-9.:/ \(\)]{32}) (-?\d+)[ ]+(?:([A-Za-z0-9.:/ \(\)]{24}) (-?\d+)[ ]+)?$")
regex_ap_counters3 = re.compile(
    br"^((?:TOTL|:[0-9 ][0-9]\.[0-9])):[ ]+(\d+)[ ]+(\d+)[ ]+(\d+)[ ]+(\d+)[ ]+(\d+)[ ]+(\d+)[ ]+(\d+)[ ]+(\d+)[ ]+(\d+)$")

regex_user_stats = re.compile(br"^([RT]x (?:Multicast|Unicast))[\t ]+(\d+)[\t ]+(\d+)[ ]*$")
regex_user_property = re.compile(br"^([A-Z][A-Za-z/ -6()]{1,19}):[ ]+([^\r]+)$")
regex_user_property_continue = re.compile(br"^[ ]{20}([^\r]+)$")


class WLANControllerCLI:
    def __init__(self, hostname, port, username, password):
        self.tn = telnetlib.Telnet(hostname, port)
        self.tn.read_until(b"Username: ")
        self.tn.write(bytes(username + "\r\n", 'utf-8'))
        self.tn.read_until(b"Password: ")
        self.tn.write(bytes(password + "\r\n", 'utf-8'))
        self.tn.read_until(b"Mainframe-WLAN-backup> ")
        self.tn.write(b"enable\r\n")
        self.tn.read_until(b"Enter password: ")
        self.tn.write(bytes(password + "\r\n", 'utf-8'))
        self.tn.read_until(b"Mainframe-WLAN-backup# ")
        self.data = {}
        self.userdata = {}

    def __handle_more(self):
        self.tn.write(b" ")
        self.tn.read_until(
            b"\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08\x08 \x08")

    def __run_command(self, command, expected_data_regex, handle_data_regex_match):
        self.tn.write(b"%s\r\n" % command)

        command_response = []
        while True:
            data = self.tn.expect([regex_prompt, regex_more, expected_data_regex], 5)

            if data[0] == 0:
                # was the prompt
                break
            elif data[0] == 1:
                self.__handle_more()
            elif data[0] == 2:
                command_response.append(handle_data_regex_match(data[1]))

        return command_response

    def cmd_ap_config(self):
        response = self.__run_command(b"show ap config", regex_ap_config, lambda data_match: data_match)
        for match in response:
            ap = int(match.group(1).strip())
            if ap not in self.data:
                self.data[ap] = {}
            if 1 not in self.data[ap]:
                self.data[ap][1] = {}
            if 2 not in self.data[ap]:
                self.data[ap][2] = {}
            self.data[ap]["name"] = match.group(2).strip()
            self.data[ap]["model"] = match.group(3).strip()
            self.data[ap][1]["profile"] = match.group(5).strip()
            self.data[ap][2]["profile"] = match.group(6).strip()

    def cmd_ap_status(self):
        response = self.__run_command(b"show ap status all", regex_ap_status, lambda data_match: data_match)
        for match in response:
            ap = int(match.group(1))
            if ap not in self.data:
                self.data[ap] = {}
            if 1 not in self.data[ap]:
                self.data[ap][1] = {}
            if 2 not in self.data[ap]:
                self.data[ap][2] = {}

            if match.group(2)[0] == b"o":
                self.data[ap]["state"] = "operational"
            elif match.group(2)[0] == b"c":
                self.data[ap]["state"] = "configuring"
            elif match.group(2)[0] == b"b":
                self.data[ap]["state"] = "booting"
            elif match.group(2)[0] == b"d":
                self.data[ap]["state"] = "download"
            elif match.group(2)[0] == b"x":
                self.data[ap]["state"] = "offline"

            if match.group(3).strip() != b"":
                self.data[ap]["ip"] = match.group(3).strip()
            if match.group(4).strip() != b"":
                self.data[ap]["model"] = match.group(4).strip()
            if match.group(5).strip() != b"":
                self.data[ap]["mac"] = match.group(5).strip()

            if match.group(6)[0] == b"E" or match.group(6)[0] == b"W" or match.group(6)[0] == b"w" or match.group(6)[0] == b"U":
                self.data[ap][1]["state"] = "enabled"
            elif match.group(6)[0] == b"S":
                self.data[ap][1]["state"] = "monitor"
            elif match.group(6)[0] == b"D":
                self.data[ap][1]["state"] = "disabled"

            if match.group(7)[0] == b"E" or match.group(7)[0] == b"W" or match.group(7)[0] == b"w" or match.group(7)[0] == b"U":
                self.data[ap][2]["state"] = "enabled"
            elif match.group(7)[0] == b"S":
                self.data[ap][2]["state"] = "monitor"
            elif match.group(7)[0] == b"D":
                self.data[ap][2]["state"] = "disabled"

            radio1_info = match.group(6)[2:].split(b"/")
            radio2_info = match.group(7)[2:].split(b"/")

            if len(radio1_info) == 2:
                self.data[ap][1]["channel"] = int(radio1_info[0])
                self.data[ap][1]["power"] = int(radio1_info[1])
            if len(radio2_info) == 2:
                self.data[ap][2]["channel"] = int(radio2_info[0])
                self.data[ap][2]["power"] = int(radio2_info[1])

            if match.group(8)[2] == b"d" and match.group(8)[5] == b"h":
                self.data[ap]["uptime"] = int(match.group(8)[0:2]) * 86400 + int(match.group(8)[0:2]) * 3600
            elif match.group(8)[5] == b"d":
                self.data[ap]["uptime"] = int(match.group(8)[0:5]) * 86400

    def cmd_ap_counters(self):
        ap = -1
        radio = -1
        response = self.__run_command(b"show ap counters", b"^([^\r\n]*)(?:\r\n|\n\r)", lambda data_match: data_match.group(1))
        for line in response:
            if line is None:
                continue

            regexdata = regex_ap_counters1.findall(line)
            if regexdata:
                ap = int(regexdata[0][0])
                radio = int(regexdata[0][1])
                if ap not in self.data:
                    self.data[ap] = {}
                if radio not in self.data[ap]:
                    self.data[ap][radio] = {}
                if b"stats" not in self.data[ap][radio]:
                    self.data[ap][radio]["stats"] = {}
                continue

            regexdata = regex_ap_counters2.findall(line)
            if regexdata:
                for pair in [(regexdata[0][0], regexdata[0][1]), (regexdata[0][2], regexdata[0][3])]:
                    if pair[0] and pair[1]:
                        key = pair[0].strip()[0:-1]
                        val = int(pair[1])
                        if key == b"User sessions":
                            self.data[ap][radio]["clients"] = val
                        elif key == b"Clients in power save mode":
                            self.data[ap][radio]["clients-in-power-save-mode"] = val
                        elif key == b"Radio resets":
                            self.data[ap][radio]["reset-counter"] = val
                        elif key == b"Transmit retries":
                            self.data[ap][radio]["transmit-retries"] = val
                        elif key == b"Client Rexmit Bytes":
                            self.data[ap][radio]["retransmitted-bytes"] = val
                        elif key == b"Radio adjusted Tx power":
                            self.data[ap][radio]["tx-power"] = val
                        elif key == b"Noise floor":
                            self.data[ap][radio]["noise-floor"] = val
                        elif key == b"Failed Associations":
                            self.data[ap][radio]["failed-associations"] = val
                        elif key == b"Rx/Tx Cntl/Mgmt Frames":
                            self.data[ap][radio]["rx-tx-control-management-frames"] = val
                        else:
                            pass
                            # we ignore some info
                            # print "AP %d-%d | %-32s %d" % (ap, radio, key, val)
                continue

            regexdata = regex_ap_counters3.findall(line)
            if regexdata:
                speed = regexdata[0][0]
                if speed == b"TOTL":
                    speed = b"sum"
                else:
                    speed = speed.strip()
                if speed not in self.data[ap][radio]["stats"]:
                    self.data[ap][radio]["stats"][speed] = {}
                self.data[ap][radio]["stats"][speed]["tx-unicast-pkts"] = int(regexdata[0][1])
                self.data[ap][radio]["stats"][speed]["tx-unicast-bytes"] = int(regexdata[0][2])
                self.data[ap][radio]["stats"][speed]["tx-multicast-pkts"] = int(regexdata[0][3])
                self.data[ap][radio]["stats"][speed]["tx-multicast-bytes"] = int(regexdata[0][4])
                self.data[ap][radio]["stats"][speed]["rx-pkts"] = int(regexdata[0][5])
                self.data[ap][radio]["stats"][speed]["rx-bytes"] = int(regexdata[0][6])
                # ignore undcrypt pkts & bytes (7+8)
                self.data[ap][radio]["stats"][speed]["phy-error"] = int(regexdata[0][9])
                continue

    def __timestr_to_timestamp(self, str):
        # no time given
        if str == b"-":
            return 0
        #  remove (... ago) suffix
        if b"(" in str:
            str = str.split(b"(")[0].strip()
        date = dateparser.parse(str)
        return calendar.timegm(date.timetuple())

    def cmd_user_sessions(self):
        session = None
        # if not None, the next empty is additional ipv6 value
        ipv6_addresses = None
        self.userdata = {}

        response = self.__run_command(b"show sessions network verbose", b"^([^\r\n]*)(?:\r\n|\n\r)", lambda data_match: data_match.group(1))
        for line in response:
            if line is None:
                continue

            regexdata = regex_user_stats.findall(line)
            if regexdata:
                ipv6_addresses = None
                type = regexdata[0][0]
                pkts = regexdata[0][1]
                bytes = regexdata[0][2]

                if not session:
                    # parsing error, continue to read the remaining command
                    continue

                if "stats" not in self.userdata[session]:
                    self.userdata[session]["stats"] = {}

                if type == b"Rx Unicast":
                    self.userdata[session]["stats"]["rx-unicast-pkts"] = int(pkts)
                    self.userdata[session]["stats"]["rx-unicast-bytes"] = int(bytes)
                elif type == b"Rx Multicast":
                    self.userdata[session]["stats"]["rx-multicast-pkts"] = int(pkts)
                    self.userdata[session]["stats"]["rx-multicast-bytes"] = int(bytes)
                elif type == b"Tx Unicast":
                    self.userdata[session]["stats"]["tx-unicast-pkts"] = int(pkts)
                    self.userdata[session]["stats"]["tx-unicast-bytes"] = int(bytes)

                continue

            regexdata = regex_user_property.findall(line)
            if regexdata:
                key = regexdata[0][0].strip()
                val = regexdata[0][1].strip()

                if key == b"IPV6 (Global)":
                    ipv6_addresses = self.userdata[session]["ipv6"] = [val]
                else:
                    ipv6_addresses = None
                    if key == b"Session ID":
                        session = int(val)
                        self.userdata[session] = {}
                    elif key == b"SSID":
                        self.userdata[session]["ssid"] = val
                    elif key == b"IP":
                        self.userdata[session]["ip"] = val
                    elif key == b"MAC":
                        self.userdata[session]["mac"] = val
                    elif key == b"AP/Radio":
                        splitted = val.split(b"/")
                        self.userdata[session]["ap"] = int(splitted[0])
                        self.userdata[session]["radio"] = int(splitted[1][0])
                    elif key == b"Host name":
                        self.userdata[session]["hostname"] = val
                    elif key == b"Vlan name":
                        val = val.replace(b"(service profile)", b"").strip()
                        self.userdata[session]["vlan"] = val
                    elif key == b"Session Start":
                        self.userdata[session]["session-start"] = self.__timestr_to_timestamp(val)
                    elif key == b"Last Auth Time":
                        self.userdata[session]["last-auth"] = self.__timestr_to_timestamp(val)
                    elif key == b"Last Activity":
                        self.userdata[session]["last-activity"] = self.__timestr_to_timestamp(val)
                    elif key == b"Last packet rate":
                        tmp = re.sub(br" \(m[0-9] [24]0MHz\)", b"", val.replace(b" Mb/s", b""))
                        tmp = tmp.replace(b".0", b"")
                        self.userdata[session]["last-rate-mbits"] = tmp
                    elif key == b"Last packet RSSI":
                        self.userdata[session]["last-rssi-dbm"] = int(val.replace(b" dBm", b""))
                    elif key == b"Last packet SNR":
                        self.userdata[session]["last-snr"] = int(val)

                continue

            if ipv6_addresses is not None:
                regexdata = regex_user_property_continue.findall(line)
                if regexdata:
                    val = regexdata[0].strip()
                    ipv6_addresses.append(val)

        return self.userdata

    def cmd_all(self):
        self.data = {}
        self.cmd_ap_config()
        self.cmd_ap_status()
        self.cmd_ap_counters()
        return self.data

    def exit(self):
        self.tn.write(b"exit\r\n")
        self.tn.read_all()
        self.tn.close()

    def clear(self):
        self.data = {}
