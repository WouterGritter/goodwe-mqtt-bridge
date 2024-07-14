import datetime
import os
import time
from dataclasses import dataclass
from typing import Optional

import paho.mqtt.client as mqtt
from pygoodwe import SingleInverter

MQTT_BROKER_ADDRESS = os.getenv('MQTT_BROKER_ADDRESS', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))
MQTT_TOPIC_FORMAT = os.getenv('MQTT_TOPIC_FORMAT', 'goodwe/{attribute}')
MQTT_QOS = int(os.getenv('MQTT_QOS', '0'))
MQTT_RETAIN = os.getenv('MQTT_RETAIN', 'true') == 'true'
GOODWE_SYSTEM_ID = os.getenv('GOODWE_SYSTEM_ID')
GOODWE_EMAIL = os.getenv('GOODWE_EMAIL')
GOODWE_PASSWORD = os.getenv('GOODWE_PASSWORD')
UPDATE_INTERVAL = float(os.getenv('UPDATE_INTERVAL', '900'))

mqttc: Optional[mqtt.Client] = None
inverter: Optional[SingleInverter] = None


@dataclass
class InverterReading:
    voltage: float  # V
    amperage: float  # A
    power: float  # W
    energy: float  # Wh


def fetch_reading():
    inverter.getCurrentReadings()
    return InverterReading(
        voltage=round(float(inverter.data['inverter']['output_voltage'][:-1]), 1),
        amperage=round(float(inverter.data['inverter']['output_current'][:-1]), 1),
        power=round(float(inverter.data['inverter']['output_power'][:-1])),
        energy=round(float(inverter.data['inverter']['total_generation'][:-3]) * 1000),
    )


def publish_mqtt(attribute: str, value: any):
    topic = MQTT_TOPIC_FORMAT.replace('{attribute}', attribute)
    mqttc.publish(topic, value, qos=MQTT_QOS, retain=MQTT_RETAIN)


def publish_reading(reading: InverterReading):
    publish_mqtt('voltage', reading.voltage)
    publish_mqtt('amperage', reading.amperage)
    publish_mqtt('power', reading.power)
    publish_mqtt('energy', reading.energy)


def update():
    reading = fetch_reading()
    publish_reading(reading)


def main():
    global mqttc, inverter

    print(f'goodwe-mqtt-bridge version {os.getenv("IMAGE_VERSION")}')

    print(f'{MQTT_BROKER_ADDRESS=}')
    print(f'{MQTT_BROKER_PORT=}')
    print(f'{MQTT_TOPIC_FORMAT=}')
    print(f'{MQTT_QOS=}')
    print(f'{MQTT_RETAIN=}')
    print(f'{GOODWE_SYSTEM_ID=}')
    print(f'{GOODWE_EMAIL=}')
    print(f'GOODWE_PASSWORD={"*" * len(GOODWE_PASSWORD)}')
    print(f'{UPDATE_INTERVAL=}')

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, 60)
    mqttc.loop_start()

    inverter = SingleInverter(
        system_id=GOODWE_SYSTEM_ID,
        account=GOODWE_EMAIL,
        password=GOODWE_PASSWORD,
    )

    start_time = datetime.time(5, 0, 0)  # 5:00 AM
    end_time = datetime.time(23, 0, 0)  # 11:00 PM

    while True:
        time.sleep(UPDATE_INTERVAL)

        current_time = datetime.datetime.now().time()
        if start_time <= current_time <= end_time:
            update()


if __name__ == '__main__':
    main()
