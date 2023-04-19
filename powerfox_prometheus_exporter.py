import re
import requests
import signal
import time
import base64
import json


from threading import Event
from click import command, option
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY, GaugeMetricFamily


OBIS_KEYS = {
  '0100010800ff': 'wirkarbeit_zaehlerstand_aplus_wh',
  '0100020800ff': 'wirkarbeit_zaehlerstand_aminus_wh',
  '0100010801ff': 'wirkenergie_tarif1_bezug_wh',
  '0100010802ff': 'wirkenergie_tarif2_bezug_wh',
  '0100100700ff': 'wirkleistung_aktuell_w'
}


def get_powerfox_metrics(hostname):
  for retry in range(0, 10):
    try:
      payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "getConfig",
        "params": { "key": "latest_data" }
      }
      rsp = requests.post('http://{}/rpc'.format(hostname), json=payload)
      if rsp.status_code != 200:
        return None
      data = rsp.json()
      data = json.loads(base64.b64decode(data['result'].encode('ascii')))
    except Exception as e:
      print('Error: {}'.format(e))
      return None

    if len(data) == 2:
      result = {
        'timestamp'         : data[0]['t'],
        'zaehlernummer'     : data[0]['m']
      }

      for item in data:
        if 'd' in item:
          for data_item in item['d']:
            o = data_item['o']
            v = data_item['v']

            if o in OBIS_KEYS:
              result[OBIS_KEYS[o]] = int(v)
            else:
              print('Unknown OBIS key: {}'.format(o))

      return result

    print('Retrying...')
    time.sleep(1)

  return None


class Collector:
  def __init__(self, powerfox_ip):
    self._powerfox_ip = powerfox_ip

  def collect(self):
    metrics = {
      'wirkarbeit_zaehlerstand_aplus_wh': GaugeMetricFamily(
        'wirkarbeit_zaehlerstand_aplus_wh',
        'Aktueller Zaehlerstand A+ in Wh',
        labels=['hostname']
      ),
      'wirkarbeit_zaehlerstand_aminus_wh': GaugeMetricFamily(
        'wirkarbeit_zaehlerstand_aminus_wh',
        'Aktueller Zaehlerstand A+ in Wh',
        labels=['hostname']
      ),
      'wirkenergie_tarif1_bezug_wh': GaugeMetricFamily(
        'wirkenergie_tarif1_bezug_wh',
        'Aktueller Zaehlerstand A+ Tarif 1 in Wh',
        labels=['hostname']
      ),
      'wirkenergie_tarif1_bezug_wh': GaugeMetricFamily(
        'wirkenergie_tarif1_bezug_wh',
        'Aktueller Zaehlerstand A+ Tarif 2 in Wh',
        labels=['hostname']
      ),
      'wirkleistung_aktuell_w': GaugeMetricFamily(
        'wirkleistung_aktuell_w',
        'Aktuelle Wirkleistung in W',
        labels=['hostname']
      )
    }

    devices = [self._powerfox_ip]
    for device_hostname in devices:
      device_metrics = get_powerfox_metrics(device_hostname)
      if device_metrics is not None:
        for key, value in device_metrics.items():
          if key in metrics:
            metrics[key].add_metric([device_hostname], value)

    for m in metrics.values():
      yield m


def graceful_shutdown(shutdown_event):
    def _handle(sig, frame):
        shutdown_event.set()
    signal.signal(signal.SIGINT, _handle)


def start_monitoring(prometheus_port, collector):
    start_http_server(prometheus_port)
    REGISTRY.register(collector)


@command()
@option('--prometheus-port', default=8080, help="Port for prometheus metric server")
@option('--powerfox-ip', required=True, help="powerfox IP address")
def run(prometheus_port, powerfox_ip):
    collector = Collector(powerfox_ip)
    start_monitoring(prometheus_port, collector)

    shutdown = Event()
    graceful_shutdown(shutdown)

    shutdown.wait()


if __name__ == '__main__':
  run()
