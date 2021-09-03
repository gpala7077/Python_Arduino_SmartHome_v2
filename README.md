# smarthome_v2


Each chip listens to a unique channel. Room and Chip name are used as part of that unique channel.

For example:
sending and receiving command to channel
home/rooms/kitchen/things/front_door/command

Chip Response (JSON)

    "group": "Kitchen",
    "room" : "MasterBedroom",
    "chip_id": "2000726507",
    "chip_name": "ChipA",
    "request_id": "9dca81bf-ba14-4840-a600-d26f1f4e3ac6",
    "response":[
            {
                "sensor_pin": "1",
                "sensor_name": "TempSensor",
                "sensor_type": "temperature",
                "sensor_value": 28
            },
            {
                "sensor_pin": "2",
                "sensor_name": "magnetSensor",
                "sensor_type": "magnet",
                "sensor_value": 1
                },
            {
                "sensor_pin": "3",
                "sensor_name": "humiditySensor",
                "sensor_type": "humidity",
                "sensor_value": 25
            }
    ]
}
