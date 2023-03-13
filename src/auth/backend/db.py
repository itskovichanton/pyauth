from typing import Protocol

from pymongo import MongoClient
from src.mybootstrap_ioc_itskovichanton.ioc import bean


class DB(Protocol):

    def get_client(self):
        ...


@bean(connection_string="db.connection-string")
class DBImpl(DB):

    def init(self, **kwargs):
        self.client = MongoClient(self.connection_string)

    def get_db(self):
        return self.client["palmautic"]
