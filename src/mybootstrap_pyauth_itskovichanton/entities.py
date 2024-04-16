from dataclasses import dataclass
from typing import TypeVar, Generic

from src.mybootstrap_mvc_itskovichanton.pipeline import Call

ID = TypeVar('ID')

ROLE_ADMIN = "admin"
ROLE_REGULAR_USER = "regular-user"


@dataclass(frozen=False)
class User(Generic[ID]):
    username: str = None
    password: str = None
    id: ID = None
    role: str = None
    lang: str = None
    name: str = None
    ip: str = None


@dataclass(frozen=False)
class Session:
    token: str = None
    account: User = None


@dataclass(frozen=True)
class AuthArgs:
    username: str = None
    password: str = None
    session_token: str = None

    def empty(self):
        return not self.username and not self.password and not self.session_token


@dataclass
class Caller:
    call: Call = None
    auth_args: AuthArgs = None
    session: Session = None
    lang: str = None
