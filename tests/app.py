from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from server import TestServer
from src.mybootstrap_pyauth_itskovichanton.backend.auth import Authentificator
from src.mybootstrap_pyauth_itskovichanton.backend.session_storage import RedisSessionStorage
from src.mybootstrap_pyauth_itskovichanton.backend.user_repo import UserRepo
from src.mybootstrap_pyauth_itskovichanton.entities import User, Session


@bean
class AuthApp(Application):
    user_repo: UserRepo
    session_storage: RedisSessionStorage
    auth: Authentificator
    server: TestServer

    def run(self):
        # self._register_user(username="guest", session_token="guest-static-session-token", id=-1, role="user")
        # self._register_user(username="admin", session_token="admin-session", id=-10, role="admin")
        a = self.session_storage.find_session(Session(token="d09daa4946c94c889c57a01fcbdd5457"))
        # b = self.session_storage.find_session(Session(token="90467291f101998e0e650af713db3c3e"))
        self.server.start()
        # self.user_repo.put(
        #     User(username="antonitskovich11", password="12345"))
        # self.user_repo.put(
        #     User(_id=ObjectId("640f9ad07b3060966080436d"), username="anton", password="12345"))

    def _register_user(self, username, session_token, id, role=None):
        if not role:
            role = "user"
        u = User(id=id, username=username, lang="ru", role=role, password=username)
        self.auth.register(u, session_token=session_token)
