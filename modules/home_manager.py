from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
from mosquitto_manager import MQTT_Client
from commands_manager import Commands
import pandas as pd


class Main:
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.mosquitto = MQTT_Client(self.mosquitto_callback)
        self.commands = Commands()
        self.requests = dict()
        self.status = None
        self.initialize()

    def initialize(self):
        """Start up program"""
        print('Initializing {} | {}'.format(self.__class__.__name__, self.data['name']))
        print(self.mosquitto.connect())  # Log info
        print(self.mosquitto.listen(self.data['mqtt_data']['subscribe']))  # Log info

    def send_request(self, request):
        """Returns current or last known status."""

        request_id = datetime.now().strftime("%m%d%Y%H%M%S")
        self.requests.update({request_id: None})

        payload = {"request_id": request_id, "request": request}  # define payload

        self.mosquitto.broadcast(self.data['mqtt_data']['publish'], payload)   # Request thing status

        return request_id

    def mosquitto_callback(self, client, userdata, message):
        """Mosquitto callback function."""
        msg = message.payload.decode("utf-8")  # Decode message
        topic = message.topic  # Get topic
        msg = msg.replace("'", "\"")  # Replace single for double quotes
        msg = json.loads(msg)  # convert string to dictionary
        print('\n{} Received message!\n{}\n{}\n'.format(self.data['name'], topic, msg))

        if 'interrupt' in topic:  # If interrupt
            print('Do something with...{}'.format(msg))

        elif 'request' in topic:  # If request
            print('Do something with {}'.format(msg))

        elif 'response' in topic:  # If response
            self.requests[msg['request_id']] = msg['response']


class Home(Main):
    def __init__(self, data):
        super().__init__(data)
        self.rooms = {room['id']: Room(room)
                      for room in self.data['rooms']}

    def send_request(self, request):
        results = []
        status = []  # Initialize empty condition list
        with ThreadPoolExecutor() as executor:  # Begin sub-threads
            for room in self.rooms:
                status.append(executor.submit(
                    self.rooms[room].send_request, request=request))  # submit to pool

            for result in as_completed(status):  # Wait until all things have been read
                results += result.result()

        self.status = results

        return self.status


class Room(Main):
    def __init__(self, data):
        super(Room, self).__init__(data)
        self.things = {thing['id']: Thing(thing)  # Create dictionary of Things
                       for thing in self.data['things']}

    def send_request(self, request):
        results = []
        status = []  # Initialize empty condition list
        with ThreadPoolExecutor() as executor:  # Begin sub-threads
            for thing in self.things:
                status.append(executor.submit(
                    self.things[thing].send_request, request=request))  # submit to pool

            for result in as_completed(status):  # Wait until all things have been read
                results += result.result()

        self.status = results

        return self.status


class Thing(Main):
    def __init__(self, data):
        super().__init__(data)

    def send_request(self, request, timeout=5):
        request_id = super(Thing, self).send_request(request)

        started = datetime.now()
        while self.requests[request_id] is None:
            if (datetime.now() - started).total_seconds() >= timeout:
                print('No Response. Device might be disconnected')
                return []

        return self.requests.pop(request_id)


if __name__ == '__main__':
    data = \
        {
            'id':   1,
            'name': 'Home',
            'mqtt_data':
                {
                    'subscribe': ['home/requests'],
                    'publish': 'home/response'
                },

            'rooms':
                [
                    {
                        'id': 1,
                        'name': 'Kitchen',
                        'mqtt_data':
                            {
                                'subscribe': ['home/rooms/kitchen/requests', 'home/rooms/kitchen/things/+/interrupt'],
                                'publish': 'home/rooms/kitchen/response'
                            },

                        'things':
                            [
                                {
                                    'id': '7503678',
                                    'name': 'Front Door',
                                    'mqtt_data':
                                        {
                                            'subscribe': ['home/rooms/kitchen/things/front_door/response'],
                                            'publish': 'home/rooms/kitchen/things/front_door/requests'
                                        }
                                }
                            ]
                    }
                ]
        }
    home = Home(data)
    print(home.send_request('status'))