import hashlib
import random
import threading
from typing import Protocol

from src.mbulak_tools.events import event_bus
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from src.mybootstrap_pyauth_itskovichanton.backend.utils import ThreadSafeImmutableDict
from src.mybootstrap_pyauth_itskovichanton.entities import User, Session

EVENT_LOGOUT = "event-logout"
EVENT_LOGIN = "event-login"


class TokenFactory(Protocol):
    def generate(self, token_to_fix: str, user: User) -> str:
        ...


@bean
class SimpleTokenFactory(TokenFactory):

    def generate(self, token_to_fix: str, user: User) -> str:
        arg = f"{token_to_fix}:{user.username}:{random.randint(10, int(10e6))}"
        return hashlib.md5(arg.encode()).hexdigest()


class SessionStorage(Protocol):

    def find_session(self, criteria: Session) -> Session:
        ...

    def logout(self, session: Session) -> Session:
        ...

    def clear(self):
        ...

    def assign_session(self, user: User, forced_session_token: str = None):
        ...

    def get_user_count(self) -> dict[str, int]:
        ...


@bean
class InMemSessionStorage(SessionStorage):
    token_factory: TokenFactory

    def init(self):
        self.lock = threading.Lock()
        self.clear()

    def find_session(self, criteria: Session) -> Session:

        if criteria.token and len(criteria.token) > 0:
            return self.token_to_session.get(criteria.token)

        token = self.username_to_token.get(criteria.account.username)
        if token:
            return self.token_to_session.get(token)

    def logout(self, criteria: Session) -> Session:
        removed_session = self.find_session(criteria)
        if removed_session:
            with self.lock:
                self.token_to_session.pop(removed_session.token)
                self.username_to_token.pop(removed_session.account.username)
                event_bus.emit(EVENT_LOGOUT, session=removed_session)
                # removed_session.account.session_token = None

        return removed_session

    def clear(self):
        self.token_to_session = ThreadSafeImmutableDict[str, Session]()
        self.username_to_token = ThreadSafeImmutableDict[str, str]()

    def assign_session(self, user: User, forced_session_token: str = None):

        self.logout(Session(account=user, token=forced_session_token))

        with self.lock:
            new_token = forced_session_token or self._calc_new_token(user)
            session = Session(token=new_token, account=user)

            self.username_to_token[user.username] = new_token
            self.token_to_session[new_token] = session

            event_bus.emit(EVENT_LOGIN, session=session)

            # user.session_token = new_token

        return session

    def _calc_new_token(self, user: User) -> str:
        # if user.session_token and len(user.session_token) > 0:
        #     return user.session_token

        r = self.token_factory.generate("", user)
        while True:
            existing_session = self.token_to_session.get(r)
            if existing_session:
                r = self.token_factory.generate(existing_session.token, user)
            else:
                break

        return r

    def get_user_count(self) -> dict[str, int]:
        return {"username_to_token": len(self.username_to_token), "token_to_session": len(self.token_to_session)}
