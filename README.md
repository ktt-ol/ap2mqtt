# ap2mqtt

Reads various data from our access points via telnet and forward that using mqtt. 

# Install

**venv**

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Debian**

```bash
apt-get install python3-sdnotify python3-dateutil python3-paho-mqtt 
```

# Run

Create the configuration and change it to your needs.
```bash
cp ap2mqtt.conf.example ap2mqtt.conf
vim ap2mqtt.conf
```

Start:
```bash
source venv/bin/activate
./ap2mqtt.py
```

# Doc

Sends on the `session-path` topic json like this:

```json
[{"ipv4": "192.99.99.99", "ipv6": ["ipv6 1...", "ipv6 2..."], "mac": "18:fe:ab:ab:ab:ab", "ap": 105, "location": "Space"} ]
```


Ruckus client sample data:
```
  Clients:
    Mac Address= a4:f1:00:00:00:00
    User/IP= 192.168.00.00
    Access Point= c4:10:00:00:00:00
    BSSID= c4:10:00:00:00:00
    Connect Since=2020/09/20 18:39:21
    Auth Method= OPEN
    WLAN= mainframe
    VLAN= 42
    Channel= 108
    Radio= 802.11an
    Signal= 0
    Status= Authorized

```

Ruckus ap data:
```
    6:
      MAC Address= c4:01:00:00:00:00
      Model= zf7363
      Approved= Yes
      Device Name= Flur-hinten
      Description= 106
      Location= Space
      GPS= 
      Group Name= System Default
      Radio a/n:
        Channelization= 40
        Channel= Auto
        WLAN Services enabled= Yes
        5.8GHz Channels = Disabled
        Tx. Power= Auto
        WLAN Group Name= OG2-5GHz
      Radio b/g/n:
        Channelization= 20
        Channel= Auto
        WLAN Services enabled= Yes
        5.8GHz Channels = Disabled
        Tx. Power= Auto
        WLAN Group Name= OG2-2.4GHz
      Override global ap-model port configuration= No
      Network Setting:
        Protocol mode= IPv4-Only
        Device IP Settings= Keep AP's Setting
        IP Type= DHCP
        IP Address= 192.168.00.00
        Netmask= 255.255.255.0
        Gateway= 192.168.00.00
        Primary DNS Server= 192.168.00.00
        Secondary DNS Server= 
      Mesh:
        Status= Disabled
```
