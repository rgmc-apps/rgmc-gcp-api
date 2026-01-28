import os
import sqlalchemy
import config
import mappings
from urllib.parse import quote_plus
from google.cloud.sql.connector import Connector

class DbConn(object):
    def __init__(self, logger, db_name='master'):
        self.__db_name = db_name

        if db_name in mappings.db_mappings:
            self.__db_name = mappings.db_mappings[db_name]
    
    def get_mssql_engine(self):
        connector = Connector()

        def getconn():
            conn = connector.connect(
                config.mssql_instance,
                driver="pytds",
                user=config.mssql_user,
                password=config.mssql_password,
                db=config.mssql_database,
            )
            return conn

        engine = sqlalchemy.create_engine(
            "mssql+pytds://",
            creator=getconn,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        return engine

    def main(self):
        engine = self.get_mssql_engine()
        return engine
    