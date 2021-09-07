import sqlalchemy
import pandas as pd
from config.configurations import database


class Database:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(
            'mysql+pymysql://{username}:{password}@{host_ip}:3306/{database}'.format(**database))

    def query(self, query):
        return pd.read_sql(query, self.engine)

    def insert(self, data, table):
        data.to_sql(self.engine, table, if_exists='APPEND')
        return 'Inserted Data'
