# smarthome_v2


Each chip listens to a unique channel. Room and Chip name are used as part of that unique channel.

For example:
sending and receiving command to channel
home/rooms/kitchen/things/front_door/requests

Hub Request (JSON)
{
    "request_id": '09042021013158', 
    "command": "status"
}

Chip Response (JSON)
{
    'request_id': '09042021013158', 
    'response': 
        [
            {
                'sensor_name': 'temp/humid', 
                'sensor_type': 'temperature', 
                'sensor_pin': 2, 
                'sensor_value': 28
            }, 
            {
                'sensor_name': 'temp/humid', 
                'sensor_type': 'humidity', 
                'sensor_pin': 2, 
                'sensor_value': 25
            }, 
            {
                'sensor_name': 'front_door', 
                'sensor_type': 'magnet', 
                'sensor_pin': 0, 
                'sensor_value': 1
            }
        ]
}