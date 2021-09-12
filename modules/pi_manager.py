import Adafruit_ADS1x15
import Adafruit_DHT
import RPi.GPIO as GPIO
import json
import pandas as pd

from modules.mosquitto_manager import MQTT_Client
from modules.miscellaneous import Queue
from threading import Thread


def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial.lstrip('0')


class MCU:
    """Represents a Raspberry Pi and it's attached sensors.

    Attributes
    ----------
    GPIO : object
        GPIO object from RPi.GPIO

    data : dict
        Dictionary defined as {name_of_data: DataFrame}

    bounce_time : int
        Bounce time for pin reset

    interrupts : object
        Object of type Queue, manages list of interrupts

    Parameters
    ----------
    data : dict
        Dictionary defined as {name_of_data: DataFrame}
    """

    def __init__(self, data, interrupt_callback):
        print('Starting up the Raspberry Pi.')
        self.GPIO = GPIO  # Set attributes
        self.data = pd.DataFrame(data)
        self.bounce_time = 8000
        self.interrupts = Queue('LIFO')
        self.interrupt_callback = interrupt_callback

    def start(self):
        """Start the Raspberry Pi."""

        print('Configuring warnings and board pin outs...')
        self.GPIO.setwarnings(False)  # Turn off warnings
        self.GPIO.setmode(self.GPIO.BCM)  # Set references as BCM
        self.initialize()  # Initialize Raspberry Pi

        return 'Raspberry Pi is up and running\n'

    def configure_pin(self, pin_id, pin_type, pin_up_down):
        """Configures a pin on the raspberry pi."""
        if pin_type == 'input' and pin_up_down == 'up':
            self.GPIO.setup(pin_id, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)

        elif pin_type == 'input' and pin_up_down == 'down':
            self.GPIO.setup(pin_id, self.GPIO.IN, pull_up_down=self.GPIO.PUD_DOWN)

        elif pin_type == 'input' and pin_up_down == 'none':
            self.GPIO.setup(pin_id, self.GPIO.IN)

        elif pin_type == 'output' and pin_up_down == 'up':
            self.GPIO.setup(pin_id, self.GPIO.OUT, pull_up_down=self.GPIO.PUD_UP)

        elif pin_type == 'output' and pin_up_down == 'down':
            self.GPIO.setup(pin_id, self.GPIO.OUT, pull_up_down=self.GPIO.PUD_DOWN)

        elif pin_type == 'output' and pin_up_down == 'none':
            self.GPIO.setup(pin_id, self.GPIO.OUT)

    def configure_interrupt(self, pin_id, interrupt_on):
        """Configures a software-based interrupt."""

        if interrupt_on == 'rising':  # If pin value rises
            self.GPIO.add_event_detect(pin_id, self.GPIO.RISING,
                                       callback=self.interrupt_callback, bouncetime=self.bounce_time)
        elif interrupt_on == 'falling':  # If pin value falls
            self.GPIO.add_event_detect(pin_id, self.GPIO.RISING,
                                       callback=self.interrupt_callback, bouncetime=self.bounce_time)
        elif interrupt_on == 'both':  # If pin falls or rises
            self.GPIO.add_event_detect(pin_id, self.GPIO.BOTH,
                                       callback=self.interrupt_callback, bouncetime=self.bounce_time)

    def initialize(self):
        """Initializes all the attached sensors."""

        print('Configuring pins...')

        for pin in self.data.to_dict(orient='records'):  # iterate through each pin
            self.configure_pin(pin['pin_id'], pin['pin_type'], pin['pin_up_down'])  # configure
            self.configure_interrupt(pin['pin_id'], pin['pin_interrupt_on'])  # set interrupt

    def read_write(self, query=None, read_write='read', write=None):
        """Reads or writes to the initialized sensors.

            Examples:
            to read all: read_write()
            to read specific: read_write('pin_id == 1')
            to read specific: read_write('pin_name == "light1"')
            to write specific: read_write('pin_id == 1', 'write', 1)

        """

        if query is None:  # Read all sensor if not specified
            data = self.data
        else:
            data = self.data.query(query)  # Specify sensors
        value = int()  # Initialize empty value
        n = len(data)  # Count total sensors
        results = []  # Create empty list
        for i in range(n):  # Iterate through each element
            current_row = data[i:i + 1].to_dict(orient='records')[0]  # Look at current row

            if read_write == 'write':  # If write
                self.GPIO.output(current_row['pin_id'], int(write))  # Write value to pin

            elif current_row['pin_type'] == 'adc':  # if sensor type is adc
                value = Adafruit_ADS1x15.ADS1115().read_adc(current_row['pin_id'], gain=1)  # read adc value

            elif current_row['pin_type'] == 'dht':  # If sensor type is dht
                humidity, temperature = Adafruit_DHT.read(Adafruit_DHT.DHT11, current_row['pin_id'])
                if humidity is None and temperature is None:
                    humidity, temperature = 0.0, 0.0
                value = {'humidity': humidity, 'temperature': temperature}  # read humidity and temperature
            else:
                value = self.GPIO.input(current_row['pin_id'])  # Read pin value

            if isinstance(value, dict):  # If value read has multiple parts, break apart based on sensor name number
                for val in value:  # iterate through read values
                    result = {
                        'sensor_name': current_row['pin_name'],
                        'sensor_type': val,
                        'sensor_pin': current_row['pin_id'],
                        'sensor_value': value[val]
                    }

                    results.append(result)
            else:
                result = {
                    'sensor_name': current_row['pin_name'],
                    'sensor_type': current_row['pin_sensor'],
                    'sensor_pin': current_row['pin_id'],
                    'sensor_value': value
                    }
                results.append(result)

        return results


class Thing_Main:
    """Represents an active MCU

    Attributes
    ----------
    data : dict
        Dictionary defined as {name_of_data: pd.DataFrame}

    r_pi : object
        Class object of type MCU

    Parameters
    ----------
    credentials : dict
        Dictionary defined as {username: un, password:pwd, host:ip, database:name}

    thing_id : int
        Primary key for thing_id
    """

    def __init__(self, data):
        self.mqtt_data = data.pop('mqtt_data')
        self.mosquitto = MQTT_Client(self.mosquitto_callback)
        self.r_pi = MCU(data.pop('sensor_data'), self.interrupt_callback)  # Initialize raspberry pi
        self.data = data

    def initialize(self):
        """Initialize Raspberry pi"""
        print('Initializing {} | {}'.format(self.__class__.__name__, self.data['name']))
        print(self.mosquitto.connect())  # Log info
        print(self.mosquitto.listen(self.mqtt_data['subscribe']))  # Log info
        print(self.r_pi.start())  # Start up the RPI

    def interrupt_callback(self, pin):
        """Process active interrupt."""
        # TODO accommodate interrupts that occur when value is dropping
        print('Processing Interrupt for {}'.__class__.__name__)  # Call super class

        result = self.r_pi.read_write('pin_id == {}'.format(pin))[0]  # Read pin value

        # THIS LINE NEEDS TO BE DYNAMIC TO EITHER RISING OR DROPPING
        val = [0, 1][self.r_pi.data.query('pin_id == {}'.format(pin))['pin_interrupt_on'].to_list()[0] ==
                     'rising']  # check if it matches interrupt

        if result['sensor_value'] == val:  # if interrupt values match
            payload = {
                'thing_id': self.data['thing_id'],
                'thing_name': self.data['name'],
                'interrupt': result
            }

            self.mosquitto.broadcast(self.mqtt_data['interrupt'], payload)

    def mosquitto_callback(self, client, userdata, message):
        """Mosquitto callback function."""
        msg = message.payload.decode("utf-8")  # Decode message
        topic = message.topic  # Get topic
        print('\n{} Received message!\n{}\n{}\n'.format(self.data['name'], topic, msg))
        msg = msg.replace("'", "\"")  # Replace single for double quotes
        msg = json.loads(msg)  # convert string to dictionary

        if 'request' in topic:  # If request
            if msg['request'] == 'status':
                payload = {
                    'request_id': msg['request_id'],
                    'thing_id': self.data['thing_id'],
                    'response': self.r_pi.read_write(),
                }
                self.mosquitto.broadcast(self.mqtt_data['publish'], payload)
