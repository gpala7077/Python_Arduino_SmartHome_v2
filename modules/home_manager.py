import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
from threading import Timer, Thread

from modules.database_manager import Database
from modules.hue_manager import Hue
from modules.ifttt_manager import WebHooks_IFTTT
from modules.sonos_manager import Sonos
from modules.mosquitto_manager import MQTT_Client
from modules.commands_manager import Command, Rule
import pandas as pd


class Main(Thread):
    def __init__(self, unique_id):
        super().__init__()
        self.mosquitto = MQTT_Client(self.mosquitto_callback)
        self.database = Database()
        self.requests = dict()
        self.third_party = dict()
        self.timers = dict()
        self.status = pd.DataFrame()
        self.children = None
        self.mqtt_data = None
        self.name = None
        self.rules = None
        self.conditions = None
        self.commands = None
        self.data = None
        self.get_data(unique_id)

    def initialize(self):
        """Start up program"""
        print('Initializing {} | {}'.format(self.__class__.__name__, self.data['name']))
        print(self.mosquitto.connect())  # Log info
        print(self.mosquitto.listen(self.mqtt_data['subscribe']))  # Log info
        print(self.initialize_third_party())

    def initialize_third_party(self):  # Initialize 3rd party apps
        """Initialize third-party applications."""

        # TODO make this dynamic
        self.third_party.update({'hue': Hue(ip_addr='192.168.50.37', user='pJPb8WW2wW1P82RKu1sHBLkEQofDMofh2yNDnXzj')})
        self.third_party.update({'sonos': Sonos('192.168.50.59')})
        self.third_party.update({'ifttt': WebHooks_IFTTT('ckcorpj6ouQG_nn2YGYyQn')})

        return 'Third-party initialized'

    def send_request(self, request):
        results = []
        status = []  # Initialize empty condition list
        with ThreadPoolExecutor() as executor:  # Begin sub-threads
            for child in self.children:
                status.append(executor.submit(
                    self.children[child].send_request, request=request))  # submit to pool

            for result in as_completed(status):  # Wait until all things have been read
                results += result.result()

        if request == 'status':
            self.status = pd.DataFrame(results)
        return results

    def mosquitto_callback(self, client, userdata, message):
        """Mosquitto callback function."""
        msg = message.payload.decode("utf-8")  # Decode message
        topic = message.topic  # Get topic
        print('\n{} Received message!\n{}\n{}\n'.format(self.data['name'], topic, msg))
        msg = msg.replace("'", "\"")  # Replace single for double quotes
        msg = json.loads(msg)  # convert string to dictionary

        if 'interrupt' in topic:  # If interrupt
            if isinstance(self, Room):  # Only execute interrupts at the room level
                self.execute(msg['interrupt'], 'interrupt')

        elif 'request' in topic:  # If request
            self.execute(msg['request'], 'request')

        elif 'response' in topic:  # If response
            self.requests[msg['request_id']] = msg['response']

    def execute(self, command, command_type):
        """Execute command."""
        if command_type == 'interrupt':
            data = self.rules.query('rule_sensor == "{}"'.format(command['sensor_type'])).to_dict(
                orient='records')  # get rules data
            command = []
            for rule in data:
                if rule['rule_function'] != 'None':
                    cmd = (  # Build command tuple
                        Command(self.commands.query('command_name == "{}"'.format(rule['rule_command'])).
                                to_dict(orient='records')[0]),

                        Command(self.commands.query('command_name == "{}"'.format(rule['rule_function'])).
                                to_dict(orient='records')[0])
                    )
                else:
                    cmd = (  # Build command tuple
                        Command(self.commands.query('command_name == "{}"'.format(rule['rule_command'])).
                                to_dict(orient='records')[0]), None)
                conditions = True
                if not self.conditions.empty:
                    conditions = self.conditions.query(  # Get all condition data
                        'rule_id == {}'.format(rule['rule_id'])).to_dict(orient='records')

                command.append(Rule(rule, cmd, conditions))  # initialize new Rule object

        elif command_type == 'command':
            if not isinstance(command, Command):
                command = Command(command)

        print(command)  # Print the canonical string representation
        if isinstance(command, Command):  # If object is of type Command
            # ***************** Phillips Hue - Third Party Commands *****************
            if command.command_type == 'hue':
                if 'hue' in self.third_party:
                    command.command_value = command.command_value.replace("'", "\"")

                    print(self.third_party['hue'].set_group(command.command_sensor, command.command_value))

            # ***************** Sonos - Third Party Commands *****************
            elif command.command_type == 'sonos':
                if command.command_sensor == 'listen' and command.command_value == 'random':
                    self.third_party['sonos'].listen()

                elif command.command_sensor == 'listen':
                    self.third_party['sonos'].listen(command.command_value)

                elif command.command_sensor == 'speak':
                    self.third_party['sonos'].player.volume += 10
                    self.third_party['sonos'].speak(command.command_value)
                    self.third_party['sonos'].player.volume -= 10

        elif len(command) > 0 and isinstance(command[0], Rule):
            status = self.get_status(current=False)  # True for current status, False for last known status.
            check_rules = []  # Initialize empty condition list
            results = []  # Initialize empty result list
            with ThreadPoolExecutor() as executor:  # Begin sub-threads
                for cmd in command:  # iterate through each command
                    check_rules.append(
                        executor.submit(self.process_rule, rule=cmd, status=status))  # submit to thread pool

                for result in as_completed(check_rules):  # Wait until all conditions have finished
                    results.append(result.result())  # Append result to result list

    def process_rule(self, rule, status):
        if rule.check_conditions(status):  # If Rule passes all conditions
            print(rule)
            if rule.rule_sensor in self.timers:  # If timer exists, cancel and replace
                self.timers[rule.rule_sensor].cancel()

            if rule.rule_timer > 0:  # Create new timer
                self.timers.update(
                    {rule.rule_sensor: Timer(
                        interval=rule.rule_timer, function=self.execute, args=[rule.commands[1], 'command']
                    )})
                self.timers[rule.rule_sensor].start()
            return self.execute(rule.commands[0], command_type='command')

    def get_data(self, unique_id):
        self.rules = self.database.query(
            'select * '
            'from rules '
            'where device_id="{}"'.format(unique_id))

        self.conditions = self.database.query(
            'select * '
            'from conditions '
            'where rule_id in '
            '(select rule_id from rules where device_id="{}")'.format(unique_id))

        self.commands = self.database.query(
            'select * '
            'from commands '
            'where device_id="{}"'.format(unique_id))

    def get_status(self, current=True):
        if current:
            self.status = pd.DataFrame(self.send_request('status'))

        return self.status

    def start(self):
        super(Main, self).start()
        self.initialize()
        if isinstance(self, Room) or isinstance(self, Home):
            for child in self.children:
                self.children[child].start()


class Home(Main):
    def __init__(self, unique_id):
        super().__init__(unique_id)
        self.children = {child: Room(child)
                         for child in self.data['rooms']}

    def get_data(self, unique_id):
        super(Home, self).get_data(unique_id)
        info = self.database.query(
            'select * '
            'from homes '
            'where home_id="{}"'.format(unique_id)).to_dict(orient='records')[0]

        self.data = {
            'device_id': info['home_id'],
            'name': info['home_name'],
            'description': info['home_description'],
            'rooms': self.database.query(
                'select room_id '
                'from rooms '
                'where home_id="{}"'.format(unique_id))['room_id'].tolist(),
        }

        self.mqtt_data = {
            'subscribe': self.database.query(
                'select channel_broadcast '
                'from mosquitto_channels '
                'where info_level=1 and channel_type="requests"')['channel_broadcast'].tolist(),

            'publish': self.database.query(
                'select channel_broadcast '
                'from mosquitto_channels '
                'where info_level=1 and channel_type="response"')['channel_broadcast']
        }


class Room(Main):
    def __init__(self, data):
        super(Room, self).__init__(data)
        self.children = {child: Thing(child)  # Create dictionary of Things
                         for child in self.data['things']}

    def get_data(self, unique_id):
        super(Room, self).get_data(unique_id)
        info = self.database.query(
            'select * '
            'from rooms '
            'where room_id="{}"'.format(unique_id)).to_dict(orient='records')[0]

        self.data = {
            'device_id': info['room_id'],
            'name': info['room_name'],
            'description': info['room_description'],
            'things': self.database.query(
                'select thing_id '
                'from things '
                'where room_id="{}"'.format(unique_id))['thing_id'].tolist(),
        }

        self.mqtt_data = {
            'subscribe': self.database.query(
                'select channel_broadcast '
                'from mosquitto_channels '
                'where info_level=2 and channel_type in ("requests","interrupt")')
                .replace('room_name', self.data['name'].replace(' ', '_').lower(), regex=True)['channel_broadcast']
                .tolist(),

            'publish': self.database.query(
                'select channel_broadcast '
                'from mosquitto_channels '
                'where info_level=2 and channel_type="response"')
                .replace('room_name', self.data['name'].replace(' ', '_').lower(), regex=True)['channel_broadcast']
                .tolist()[0]
        }


class Thing(Main):
    def __init__(self, data):
        super().__init__(data)

    def send_request(self, request, timeout=20):
        request_id = datetime.now().strftime("%m%d%Y%H%M%S")
        self.requests.update({request_id: None})

        payload = {"request_id": request_id, "request": request}  # define payload

        self.mosquitto.broadcast(self.mqtt_data['publish'], payload)  # Request

        started = datetime.now()
        try:
            while self.requests[request_id] is None:
                if (datetime.now() - started).total_seconds() >= timeout:
                    print('No Response. Device might be disconnected')
                    return []
            return self.requests.pop(request_id)
        except:
            print('Error occurred with {}'.format(self.__class__.__name__))

    def get_data(self, unique_id):
        super(Thing, self).get_data(unique_id)
        info = self.database.query(
            'select * '
            'from things '
            'where thing_id="{}"'.format(unique_id)).to_dict(orient='records')[0]

        self.data = {
            'device_id': info['thing_id'],
            'room_id': info['room_id'],
            'room_name': self.database.query(
                'select room_name '
                'from rooms '
                'where room_id ="{}"'.format(info['room_id']))['room_name'].tolist()[0],
            'name': info['thing_name'],
            'description': info['thing_description']
        }

        self.mqtt_data = {
            'subscribe': self.database.query(
                'select channel_broadcast '
                'from mosquitto_channels '
                'where info_level=3 and channel_type in ("response", "interrupt")')
                .replace('room_name', self.data['room_name'].replace(' ', '_').lower(), regex=True)
                .replace('thing_name', self.data['name'].replace(' ', '_').lower(), regex=True)[
                'channel_broadcast'].tolist(),

            'publish': self.database.query(
                'select channel_broadcast '
                'from mosquitto_channels '
                'where info_level=3 and channel_type="requests"')
                .replace('room_name', self.data['room_name'].replace(' ', '_').lower(), regex=True)
                .replace('thing_name', self.data['name'].replace(' ', '_').lower(), regex=True)[
                'channel_broadcast'].tolist()[0],

        }
