from datetime import datetime
import json

from mosquitto_manager import MQTT_Client
import pandas as pd


class Main:
    def __init__(self, data):
        self.data = data
        self.mosquitto = MQTT_Client()
        self.new_status_flag = False
        self.status = pd.DataFrame()

    def initialize(self):
        """Start up program"""
        print('Initializing {} | {}'.format(self.__class__.__name__, self.data['name']))
        self.mosquitto.name = self.data['name']
        self.mosquitto.process_message = self.process_message               # Define callback

        print(self.mosquitto.connect())  # Log info
        print(self.mosquitto.listen(self.data['mqtt_data']['listen']))  # Log info

    def process_message(self):
        topic, msg = self.mosquitto.messages.get()

        if 'interrupt' in topic:  # If interrupt
            msg = msg.replace("'", "\"")  # Replace single for double quotes
            msg = json.loads(msg)  # convert string to dictionary
            msg = pd.DataFrame.from_dict(msg)  # Convert dictionary to data frame
            print('Do something with...{}'.format(msg))

        elif 'commands' in topic:  # If command
            print('Do something with {}'.format(msg))

        elif 'info' in topic:  # If info
            self.new_status_flag = True
            msg = msg.replace("'", "\"")  # Replace single for double quotes
            msg = json.loads(msg)  # convert to dictionary
            self.status = pd.DataFrame.from_dict(msg['status'])  # Convert to data frame and replace sensors


class Thing(Main):
    def __init__(self, data):
        super().__init__(data)

    def current_status(self, current=True):
        """Returns current or last known status."""

        print(
            'Getting {} status for {} | {}'.format(['last known', 'current'][(current == True)],
                                                   self.__class__.__name__, self.data['name']))
        if current:
            payload = """{"command":"status"}"""  # define payload
            channel = self.data['mqtt_data']['channels']['command']  # Prepare channel
            self.mosquitto.broadcast(channel, payload)  # Request thing status

            retry = 3
            timeout = 10
            started = datetime.now()
            i = 0
            self.new_status_flag = False
            while not self.new_status_flag:
                if (datetime.now() - started).total_seconds() >= timeout and i <= retry:
                    print('\nNo Response...Reattempting. Attempted {} time(s)'.format(i))
                    self.mosquitto.broadcast(channel, payload)  # Request thing status
                    started = datetime.now()
                    i += 1
                elif i > retry:
                    if not self.status.empty:
                        print('\nNo Response, sending last known status')
                        return self.status
                    else:
                        return '\nNo Response'

            self.new_status_flag = False
        return self.status


if __name__ == '__main__':
    data = {
        'mqtt_data': {
            'listen': ['home/rooms/kitchen/things/front_door/info'],
            'channels': {
                'command': 'home/rooms/kitchen/things/front_door/commands'
            }
        },
        'name': 'Front Door'
    }

    front_door = Thing(data)
    front_door.initialize()
    print(front_door.current_status())
