from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from src.mybootstrap_pyauth_itskovichanton.entities import User


class UserRepo(Protocol):

    def put(self, a: User):
        ...

    def find(self, criteria: User) -> User:
        ...


@bean
class InMemUserRepo(UserRepo):

    def __init__(self):
        self.storage = dict[str, User]()

    def put(self, a: User):
        self.storage[a.username] = a

    def find(self, criteria: User) -> User:
        return self.storage.get(criteria.username)
