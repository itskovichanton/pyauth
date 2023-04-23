from bson import ObjectId
from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from src.mybootstrap_pyauth_itskovichanton.backend.user_repo import UserRepo
from src.mybootstrap_pyauth_itskovichanton.entities import User


@bean
class AuthApp(Application):
    user_repo: UserRepo

    def run(self):
        self.user_repo.put(
            User(username="antonitskovich11", password="12345"))
        self.user_repo.put(
            User(_id=ObjectId("640f9ad07b3060966080436d"), username="anton", password="12345"))
