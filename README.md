# smarthome_v2


Each chip listens to a unique channel. Room and Chip name are used as part of that unique channel.

Assuming the following:
sending request on: home/rooms/kitchen/things/front_door/requests

receiving response on: home/rooms/kitchen/things/front_door/response


# Scenario 1: Requesting a status update

```python
# Hub Request (JSON)

{
    "request_id": '09042021013158', 
    "request": "status"
}

# Chip Response (JSON)
{
    'request_id': '09042021013158',
    'thing_id': '234541114',
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
```

# Scenario 2 - Requesting to turn on a relay
```python
# Hub Request (JSON)
{
    "request_id": '09042021013159', 
    "command": "light1_ON"
}

# Chip Response (JSON)
{
    'request_id': '09042021013159', 
    'response': 'Success'
}
```