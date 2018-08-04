from datetime import datetime
import sys
import time
from threading import Thread

from pytz import timezone
from mqtt_base import MQTTBase
from interpolater import Interpolater


class Redshift(MQTTBase):
    SCHEDULE = [
        {
            'time': '00:00',
            'temperature': 370,
            'brightness': 128
        },
        {
            'time': '02:00',
            'temperature': 370,
            'brightness': 48
        },
        {
            'time': '06:00',
            'temperature': 370,
            'brightness': 48
        },
        {
            'time': '08:00',
            'temperature': 310,
            'brightness': 255
        },
        {
            'time': '22:00',
            'temperature': 310,
            'brightness': 255
        },
    ]

    def __init__(self, config_file):
        MQTTBase.__init__(self, config_file)
        self._interpolater = Interpolater(self.SCHEDULE)

        self._topic_prefix = self.mqtt_config['topic_prefix']
        self._timezone = timezone(self.mqtt_config['timezone'])
        self._keepon = True
        self._thread = None
        self._previous_values = {}

    def on_connect(self, client, userdata, flags, conn_result):
        print("connected.")
        self._start_timer()

    def _start_timer(self):
        self._thread = Thread(target=self._worker)
        self._thread.start()

    def stop(self):
        self.disconnect()
        self._keepon = False
        if self._thread:
            self._thread.join()

    def _publish_entry(self, entry):
        for key, value in entry.items():
            new_val = str(int(round(value)))

            if self._previous_values.get(key, None) != new_val:
                topic = "{}/{}/set".format(self._topic_prefix, key)
                print("publish to {}: {}".format(topic, new_val))
                self.mqtt.publish(topic, new_val, retain=True)
                self._previous_values[key] = new_val

    def _worker(self):
        while self._keepon:
            entry = self._interpolater.interpolate_now(datetime.now(self._timezone))
            self._publish_entry(entry)
            i = 2
            while self._keepon and i > 0:
                i -= 1
                time.sleep(1)

def main():
    try:
        a = Redshift(sys.argv[1])
        a.connect()
        a.loop_forever()
    except KeyboardInterrupt:
        a.stop()

if __name__ == '__main__':
    main()
