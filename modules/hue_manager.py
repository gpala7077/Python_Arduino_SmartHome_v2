import json

import requests


class Hue:
    """Third-Party API representing Hue Light bulbs

    Attributes
    ----------
    ip_address : str
        IP address of phillips hue hub
    user : str
        User name for phillips hue hub
    data : json
        Json object containing all the data in Phillips hue

    """

    def __init__(self, ip_addr, user):
        self.ip_addr = ip_addr  # Set phillips ip address
        self.user = user  # Set user
        self.data = None  # Initialize empty data
        self.load()  # Load all data

    def load(self):
        url = 'http://{}/api/{}'.format(self.ip_addr, self.user)
        get_data = requests.get(url=url)
        self.data = get_data.json()
        return self.data

    def set_light(self, hue_id, light_command):
        """Set a single light.

        Parameters
        ----------
        hue_id : int
            Primary key for phillips light bulb
        light_command : str
            A string representation of a dictionary. i.e. {"bri": 50, "on": false}

        """

        url = 'http://{}/api/{}/lights/{}/state'.format(self.ip_addr, self.user, hue_id)
        response = requests.put(url=url, data=light_command).json()
        return response

    def set_group(self, group_id, group_command):
        """Set a group of lights.

        Parameters
        ----------
        group_id : int
            Primary key for phillips hue group
        group_command : str
            A string representation of a dictionary. i.e. '{"bri": 50, "on": false}'

        """

        url = 'http://{}/api/{}/groups/{}/action'.format(self.ip_addr, self.user, group_id)
        response = requests.put(url=url, data=group_command).json()
        return response

    def get_group(self, group_id):
        """Returns phillip's hue group data"""
        url = 'http://{}/api/{}/groups/{}'.format(self.ip_addr, self.user, group_id)
        response = requests.get(url=url).json()
        return response

    def add_group(self, group_name, hue_lights):
        """Adds a new defined group into Phillip's Hue

        Parameters
        ----------
        group_name : str
            Name of new phillips hue group
        hue_lights : list
            List of primary light bulb IDs
        """

        group_command = {
            'name': group_name,
            'lights': hue_lights
        }

        group_command = json.dumps(group_command)
        url = 'http://{}/api/{}/groups/'.format(self.ip_addr, self.user)
        response = requests.post(url=url, data=group_command).json()
        return response
