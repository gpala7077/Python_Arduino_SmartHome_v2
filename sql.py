import sqlite3
from sqlite3 import Error

'''
{
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
'''
def create_connection(db_file):

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):

    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)


def main():
    database = "smarthome.db"

    sql_create_projects_table = """ CREATE TABLE IF NOT EXISTS Chip (
                                        chip_id integer PRIMARY KEY,
                                        group text NOT NULL,
                                        room text,
                                        chip_name text
                                    ); """

    sql_create_tasks_table = """CREATE TABLE IF NOT EXISTS Sensors (
                                    id integer PRIMARY KEY,
                                    sensor_pin text NOT NULL,
                                    sensor_name text,
                                    sensor_type integer NOT NULL,
                                    chip_id integer NOT NULL,
                                    sensor_value text NOT NULL,
                                    FOREIGN KEY (chip_id) REFERENCES Chip (chip_id)
                                );"""

    conn = create_connection(database)

    if conn is not None:
        create_table(conn, sql_create_projects_table)

        create_table(conn, sql_create_tasks_table)
    else:
        print("Error! cannot create the database connection.")
