import base64
import random
from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from src.mybootstrap_pyauth_itskovichanton.entities import User, Session


class TokenFactory(Protocol):
    def generate(self, user: User) -> str:
        ...


@bean
class SimpleTokenFactory(TokenFactory):

    def generate(self, user: User) -> str:
        arg = f"{user.username}:{random.randint(10, int(10e6))}"
        return str(base64.standard_b64encode(arg))


class SessionStorage(Protocol):

    def find_session(self, criteria: Session) -> Session:
        ...

    def get_session_by_token(self, token: str) -> Session:
        ...

    def logout(self, session: Session) -> Session:
        ...

    def clear(self):
        ...

    def assign_session(self, user: User) -> Session:
        ...


@bean
class InMemSessionStorage(SessionStorage):
    token_factory: TokenFactory

    def init(self):
        self.clear()

    def find_session(self, criteria: Session) -> Session:

        if len(criteria.token) > 0:
            return self.token_to_session.get(criteria.token)

        token = self.username_to_token.get(criteria.account.username)
        if token:
            return self.token_to_session.get(token)

    def logout(self, criteria: Session) -> Session:
        removed_session = self.find_session(criteria)
        if removed_session:
            self.token_to_session.pop(removed_session.token)
            self.username_to_token.pop(removed_session.account.username)

        return removed_session

    def clear(self):
        self.token_to_session = dict[str, Session]()
        self.username_to_token = dict[str, str]()

    def assign_session(self, user: User):
        self.logout(Session(account=user, token=user.session_token))

        token = self.username_to_token.get(user.username)
        if not token:
            token = self._calc_new_token(user)
            self.username_to_token[user.username] = token

        session = self.username_to_token.get(token)
        if not session:
            session = Session(token=token, account=user)
            self.token_to_session[token] = session

        user.session_token = token
        return session

    def _calc_new_token(self, user: User) -> str:
        if len(user.session_token) > 0:
            return user.session_token

        r = self.token_factory.generate(user)
        while self.token_to_session.get(r):
            r = self.token_factory.generate(user)

        return r
