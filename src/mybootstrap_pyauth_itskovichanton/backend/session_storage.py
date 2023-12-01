import hashlib
import random
import threading
from typing import Protocol, Callable

from src.mbulak_tools.events import event_bus
from src.mybootstrap_core_itskovichanton.redis_service import RedisService
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from src.mybootstrap_pyauth_itskovichanton.backend.utils import RedisSessionMap, RedisStringMap
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

    def logout_all(self):
        ...

    def assign_session(self, user: User, forced_session_token: str = None):
        ...

    def get_token_to_session_storage(self):
        ...

    def get_username_to_token_storage(self):
        ...

    def set_user_class(self, user_class=User):
        ...


@bean
class RedisSessionStorage(SessionStorage):
    token_factory: TokenFactory
    config_service: ConfigService
    redis_service: RedisService

    def init(self):
        self.lock = threading.Lock()
        self.rds = self.redis_service.get()

        key_prefix = self.config_service.get_config().full_name()
        self.token_to_session = RedisSessionMap(key_prefix=f"{key_prefix}-ts", rds=self.rds)
        self.username_to_token = RedisStringMap(key_prefix=f"{key_prefix}-ut", rds=self.rds)

    def set_user_class(self, user_class=User):
        self.token_to_session.set_user_class(user_class)

    def find_session(self, criteria: Session) -> Session:

        if criteria.token and len(criteria.token) > 0:
            return self.token_to_session.get(criteria.token)

        token = self.username_to_token.get(criteria.account.username)
        if token:
            session = self.token_to_session.get(token)
            if session:
                return session
            self.username_to_token.delete(criteria.account.username)

    def logout(self, criteria: Session) -> Session:
        removed_session = self.find_session(criteria)
        if removed_session:
            with self.lock:
                self.token_to_session.delete(removed_session.token)
                self.username_to_token.delete(removed_session.account.username)
                event_bus.emit(EVENT_LOGOUT, session=removed_session)
                # removed_session.account.session_token = None

        return removed_session

    def logout_all(self):
        self.rds.flushdb()

    def assign_session(self, user: User, forced_session_token: str = None):

        self.logout(Session(account=user, token=forced_session_token))

        with self.lock:
            new_token = forced_session_token or self._calc_new_token(user)
            session = Session(token=new_token, account=user)

            self.username_to_token.set(user.username, new_token)
            self.token_to_session.set(new_token, session)

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

    def update_session(self, token: str, updater: Callable[[Session, ], None]) -> Session:
        return self.token_to_session.update(token, updater)

    def get_token_to_session_storage(self):
        return self.token_to_session.get_all()

    def get_username_to_token_storage(self):
        return self.username_to_token.get_all()
