from typing import Protocol

from pymongo import MongoClient
from pymongo.database import Database
from src.mybootstrap_ioc_itskovichanton.ioc import bean


class DB(Protocol):

    def get_db(self) -> Database:
        ...


@bean(connection_string="db.connection-string", dbname="db.name")
class MongoDBImpl(DB):

    def init(self, **kwargs):
        self.client = MongoClient(self.connection_string)

    def get_db(self) -> Database:
        return self.client[self.dbname]
