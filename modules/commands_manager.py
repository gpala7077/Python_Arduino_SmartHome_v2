import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Timer

import pandas as pd


class Condition:
    """Represents a single condition to a rule.

    Attributes
    -----------
    rule_id : int
        Primary record ID in Database for condition

    condition_type : str
        Type of condition i.e average, sum, max, min

    condition_check: str
        Type of sensors or specific sensor. i.e. LDR, LDR1, lights, motion, motion2

    condition_logic : str
        Type of logic to apply condition. i.e. <, <=, >, >=, etc...

    condition_value : int
        Condition threshold to test live values.
        

    Parameters
    ----------
    data : dict
        Dictionary defined as {condition_name: condition_value}

    """

    def __init__(self, data):
        self.rule_id = data['rule_id']  # Set attributes
        self.condition_type = data['condition_type']
        self.condition_check = data['condition_check']
        self.condition_logic = data['condition_logic']
        self.condition_value = data['condition_value']

    def condition_met(self, data):
        """Checks if condition is met. Returns True if met, False if not.

        Parameters
        ----------
        data : DataFrame
            Pandas data frame containing the filtered data for condition.
        """

        if self.condition_type == 'sum':  # Check sum
            return eval('{}{}{}'.format(data['sensor_value'].sum(), self.condition_logic, self.condition_value))

        elif self.condition_type == 'average':  # Check mean
            return eval('{}{}{}'.format(data['sensor_value'].mean(), self.condition_logic, self.condition_value))

        elif self.condition_type == 'time':  # Check time constraints
            now = datetime.now()  # initialize datetime now variable
            current_time = now.strftime("%H:%M")  # reformat current time

            if self.condition_logic == '>':  # Check constraints
                return current_time > self.condition_value

            elif self.condition_logic == '>=':
                return current_time >= self.condition_value

            elif self.condition_logic == '<':
                return current_time < self.condition_value

            elif self.condition_logic == '<=':
                return current_time <= self.condition_value

            elif self.condition_logic == '==':
                return current_time == self.condition_value

            elif self.condition_logic == '!=':
                return current_time != self.condition_value


class Rule:
    """Represents a smart home rule.

    Attributes
    ----------
    rule_id : int
        Primary key for rule

    info_id : int
        Primary key for room/thing

    info_level: int
        Level of control. (i.e. 1 = home, 2 = room, 3 = thing)

    rule_name : str
        Name of rule

    commands : tuple
        A tuple containing 1 or 2 commands of class type Command. (cmd1, cmd2) or (cmd1)

    rule_timer : int
        Number of seconds before executing cmd2

    rule_sensor : str
        name of sensor or types of sensors that trigger the rule.

    conditions : list
        List of class type Condition

    Parameters
    ----------
    data : dict
        Dictionary containing all rule information

    commands : tuple
        A tuple containing 1 or 2 objects of class type Command. (cmd1, cmd2) or (cmd1)

    conditions : list of dict
        List of dictionaries defined as {condition_name: condition_value}

    """

    def __init__(self, data, commands, conditions):
        self.rule_id = data['rule_id']  # Set attributes
        self.rule_name = data['rule_name']
        self.commands = commands
        self.rule_timer = data['rule_timer']
        self.rule_sensor = data['rule_sensor']
        self.conditions = [Condition(condition) for condition in conditions]

    def check_conditions(self, status):
        """Simultaneously check all conditions in rule.

        Parameters
        ----------
        status : DataFrame
            Pandas data frame of all current sensors in room

        """
        conditions_check = []  # Initialize empty condition list
        results = []  # Initialize empty result list
        with ThreadPoolExecutor() as executor:  # Begin sub-threads
            for condition in self.conditions:  # iterate through each condition

                if any(char.isdigit() for char in condition.condition_check):
                    data = status.query('sensor_name == "{}"'.format(condition.condition_check))  # filter status data

                else:
                    data = status.query('sensor_type == "{}"'.format(condition.condition_check))  # filter status data

                conditions_check.append(executor.submit(condition.condition_met, data=data))  # submit to thread pool

            for result in as_completed(conditions_check):  # Wait until all conditions have finished
                results.append(result.result())  # Append result to result list

            if [True] * len(results) == results:  # If all conditions are met, return True
                return True
            else:
                return False

    def __repr__(self):
        """Canonical string representation of rule."""

        return self.rule_name


class Command:
    """Represents a single command.

    Attributes
    ----------
    info_id : int
        Primary key for room/thing

    info_level: int
        Level of control. (i.e. 1 = home, 2 = room, 3 = thing)

    command_name : str
        Name of command

    command_type : str
        Type of command

    command_sensor : str
        Type of sensor or group to send command to

    command_value : str
        Command value can be evaluated as a string, dictionary or int. Depends on type of command.

     Parameters
    ----------
    data : dict
        Dictionary containing all command information

    """

    def __init__(self, data):
        if isinstance(data, pd.DataFrame):
            data = data.to_dict(orient='records')[0]

        self.command_name = data['command_name']
        self.command_type = data['command_type']
        self.command_sensor = data['command_sensor']
        self.command_value = data['command_value']

    def get_query(self):
        """Build query to call data"""

        if any(char.isdigit() for char in self.command_sensor):
            command = 'pin_name == "{}"'.format(self.command_sensor)

        else:
            command = 'pin_sensor == "{}"'.format(self.command_sensor)

        return command

    def __repr__(self):
        """Canonical string representation of command."""

        return '{} | {} | {} | {}'.format(self.command_name, self.command_type, self.command_sensor, self.command_value)
