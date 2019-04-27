# ap2mqtt

Reads various data from our access points via telnet and forward that using mqtt. 

# Install

**venv**

```bash
python3 -m venv venv
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
