import time
from threading import Thread

import paho.mqtt.client as mqtt

from modules.miscellaneous import Queue
from config.configurations import mosquitto_ip


class MQTT_Client:
    def __init__(self):
        self.host_ip = mosquitto_ip
        self.name = None
        self.client = mqtt.Client()
        self.messages = Queue('FIFO')
        self.process_message = None

    def mosquitto_callback(self, client, userdata, message):
        """Mosquitto callback function."""

        self.add_message(message)  # Add message to queue
        Thread(target=self.process_message).start() # Process message in queue as a sub-thread

    def add_message(self, message):
        """Adds message to queue"""

        msg = message.payload.decode("utf-8")  # Decode message
        topic = message.topic  # Get topic
        print('\n{} Received message!\n{}\n{}\n'.format(self.name, topic, msg))
        self.messages.add((topic, msg))  # Add to queue

        return 'Added message to Queue\n'

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
            self.client.subscribe(channel)

        listen = Thread(target=self.client.loop_forever)  # Begin thread to loop forever.
        listen.start()

        return 'Actively Listening for Mosquitto Broadcasts\n'

    def broadcast(self, channel, payload):
        """Broadcast payload to given channels."""

        print('\n{} Broadcasting on...\n{}\nPayload : {}'.format(self.name, channel, payload))
        self.client.publish(channel, str(payload))  # publish mosquitto to broker
        return 'Payload sent\n'

