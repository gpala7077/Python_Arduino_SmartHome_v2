import json
from datetime import datetime
from threading import Thread

import paho.mqtt.client as mqtt
from config.configurations import mosquitto_ip


class MQTT_Client:
    def __init__(self, mosquitto_callback):
        self.host_ip = mosquitto_ip
        self.client = mqtt.Client()
        self.mosquitto_callback = mosquitto_callback
        self.requests = dict()

    def connect(self):
        """Connect to MQTT Broker and set callback."""

        print('Connecting to broker... {}'.format(self.host_ip))
        self.client.connect(self.host_ip)  # Connect to broker
        self.client.on_message = self.mosquitto_callback  # define callback
        return 'Connected\n'

    def listen(self, channels):
        """Creates a sub-thread and actively listens to given channels."""

        for channel in channels:  # Subscribe to every channel in the list
            print('Listening to... {}'.format(channel))
            self.client.subscribe(channel, qos=1)

        listen = Thread(target=self.client.loop_forever)  # Begin thread to loop forever.
        listen.start()

        return 'Actively Listening for Mosquitto Broadcasts\n'

    def broadcast(self, channel, payload):
        """Broadcast payload to given channel."""

        print('\nBroadcasting on...\n{}\nPayload : {}'.format(channel, payload))
        self.client.publish(channel, str(payload), qos=1, retain=True) # publish mosquitto to broker

        return '\nPayload sent'
