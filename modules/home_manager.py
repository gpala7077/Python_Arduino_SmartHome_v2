from datetime import datetime
import json

from mosquitto_manager import MQTT_Client
import pandas as pd


class Main:
    def __init__(self, data):
        self.data = data
        self.mosquitto = MQTT_Client(self.mosquitto_callback)
        self.status = pd.DataFrame()
        self.requests = dict()

    def initialize(self):
        """Start up program"""
        print('Initializing {} | {}'.format(self.__class__.__name__, self.data['name']))
        print(self.mosquitto.connect())  # Log info
        print(self.mosquitto.listen(self.data['mqtt_data']['listen']))  # Log info

    def mosquitto_callback(self, client, userdata, message):
        """Mosquitto callback function."""
        msg = message.payload.decode("utf-8")  # Decode message
        topic = message.topic  # Get topic
        msg = msg.replace("'", "\"")  # Replace single for double quotes
        print(msg)

        msg = json.loads(msg)  # convert string to dictionary
        print('\n{} Received message!\n{}\n{}\n'.format(self.data['name'], topic, msg))

        if 'interrupt' in topic:  # If interrupt
            print('Do something with...{}'.format(msg))

        elif 'request' in topic:  # If request
            print('Do something with {}'.format(msg))

        elif 'response' in topic:  # If response
            self.requests[msg['request_id']] = msg['response']


class Thing(Main):
    def __init__(self, data):
        super().__init__(data)

    def current_status(self, current=True, timeout=30):
        """Returns current or last known status."""

        print(
            'Getting {} status for {} | {}'.format(['last known', 'current'][(current == True)],
                                                   self.__class__.__name__, self.data['name']))
        if current:
            request_id = datetime.now().strftime("%m%d%Y%H%M%S")
            self.requests.update({request_id: None})

            payload = {"request_id": request_id, "command": "status"}  # define payload
            channel = self.data['mqtt_data']['channels']['command']  # Prepare channel

            self.mosquitto.broadcast(channel, payload)   # Request thing status
            started = datetime.now()

            while self.requests[request_id] is None:
                if (datetime.now() - started).total_seconds() >= timeout:
                    return 'No Response. Device might be disconnected'

            return self.requests.pop(request_id)


if __name__ == '__main__':
    data = {
        'mqtt_data': {
            'listen': ['home/rooms/kitchen/things/front_door/response'],
            'channels': {
                'command': 'home/rooms/kitchen/things/front_door/requests'
            }
        },
        'name': 'Front Door'
    }

    front_door = Thing(data)
    front_door.initialize()
    print(front_door.current_status())

    # Send and Receive example
    # Sending: """{"command":"status"}"""
    # Response: """{"status": {"sensor_types":["temperature","humidity","magnet"],"sensor_values": [28, 25, 1] }}"""
