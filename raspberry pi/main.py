from modules.pi_manager import get_serial, MCU, Thing_Main
from modules.mosquitto_manager import MQTT_Client

# TODO Initial setup data should be entered in using a configuration website hosted by the raspberry pi.
data = {
    'thing_id': get_serial(),
    'name': 'Pi Kitchen1', # Website should enter this value
    'room': 'Kitchen',
    'mqtt_data': { # This should be automated and built from the thing name and room name
        # MQTT Structure is home/rooms/room_name/things/thing_name/(requests,response,interrupt)
        'interrupt': 'home/rooms/kitchen/things/pi_kitchen1/interrupt',
        'publish': 'home/rooms/kitchen/things/pi_kitchen1/response',
        'subscribe': ['home/rooms/kitchen/things/pi_kitchen1/requests']
    },
    'sensor_data': [ # Website should be able to add and remove pins
        {
            'pin_id': 23,
            'pin_type': 'input',
            'pin_sensor': 'motion',
            'pin_name': 'motion1',
            'pin_up_down': 'down',
            'pin_interrupt_on': 'rising'
        },
        {
            'pin_id': 19,
            'pin_type': 'output',
            'pin_sensor': 'light',
            'pin_name': 'light1',
            'pin_up_down': 'none',
            'pin_interrupt_on': 'none'
        },
        {
            'pin_id': 24,
            'pin_type': 'input',
            'pin_sensor': 'window',
            'pin_name': 'window1',
            'pin_up_down': 'none',
            'pin_interrupt_on': 'none'
        },
        {
            'pin_id': 26,
            'pin_type': 'output',
            'pin_sensor': 'HVAC_fan',
            'pin_name': 'fan1',
            'pin_up_down': 'none',
            'pin_interrupt_on': 'none'
        },
        {
            'pin_id': 20,
            'pin_type': 'output',
            'pin_sensor': 'HVAC_heat',
            'pin_name': 'heat1',
            'pin_up_down': 'none',
            'pin_interrupt_on': 'none'
        },
        {
            'pin_id': 21,
            'pin_type': 'output',
            'pin_sensor': 'HVAC_cool',
            'pin_name': 'cool1',
            'pin_up_down': 'none',
            'pin_interrupt_on': 'none'
        },
        {
            'pin_id': 0,
            'pin_type': 'adc',
            'pin_sensor': 'LDR',
            'pin_name': 'LDR1',
            'pin_up_down': 'none',
            'pin_interrupt_on': 'none'
        },
        {
            'pin_id': 16,
            'pin_type': 'input',
            'pin_sensor': 'motion',
            'pin_name': 'motion2',
            'pin_up_down': 'down',
            'pin_interrupt_on': 'rising'
        },
        {
            'pin_id': 25,
            'pin_type': 'dht',
            'pin_sensor': 'temp_humidity',
            'pin_name': 'temp1',
            'pin_up_down': 'none',
            'pin_interrupt_on': 'none'
        }
    ]
}


if __name__ == '__main__':
    rpi = Thing_Main(data)
    rpi.initialize()
