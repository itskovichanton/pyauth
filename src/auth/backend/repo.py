from typing import Protocol

from src.mbulak_tools.db import DBService
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from src.auth.backend.db import DB
from src.auth.model.model import User


class UserRepo(Protocol):

    def create_or_update(self, a: User):
        ...


@bean
class UserRepoImpl(UserRepo):
    db: DB

    def create_or_update(self, a: User):
        users = self.db.get_client()["users"]
        item_2 = {
            "_id" : "U1IT00002",
            "item_name" : "Egg",
            "category" : "food",
            "quantity" : 12,
            "price" : 36,
            "item_description" : "brown country eggs"
        }
        users.insert_many([item_2])
