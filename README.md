# Prometheus exporter for powerfox poweropti

This simple prometheus exporter collects data from powerfox poweropti devices via their local
HTTP RPC endpoint. No cloud service subscription is required.

Verified with poweropti+ and a polling interval of 15 seconds.

## Usage
```
pip3 install prometheus_client
python3 ./powerfox_prometheus_exporter.py --prometheus-port 8080 --powerfox-ip 192.168.1.120
```
Replace `192.168.1.120` with your powerfox's local IP address.
