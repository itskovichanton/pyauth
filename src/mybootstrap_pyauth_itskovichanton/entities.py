"""Доменные сущности авторизации: пользователь, сессия, аргументы входа, Caller запроса."""
from dataclasses import dataclass
from typing import Generic, TypeVar

from src.mybootstrap_mvc_itskovichanton.pipeline import Call

ID = TypeVar("ID")

ROLE_ADMIN = "admin"
ROLE_REGULAR_USER = "regular-user"


@dataclass(frozen=False)
class User(Generic[ID]):
    """Учётная запись. ``password`` — секрет (хэш); в сессионном Redis его быть не должно."""

    username: str = None
    password: str = None
    id: ID = None
    role: str = None
    lang: str = None
    name: str = None
    ip: str = None
    slug: str = None


@dataclass(frozen=False)
class Session:
    """Активный вход: непрозрачный ``token`` и снимок ``account`` без пароля."""

    token: str = None
    account: User = None


@dataclass(frozen=True)
class AuthArgs:
    """Креды из запроса: либо sessionToken, либо username+password."""

    username: str = None
    password: str = None
    session_token: str = None

    def empty(self):
        """True, если ни токена, ни пары логин/пароль не передали."""
        return not self.username and not self.password and not self.session_token


@dataclass
class Caller:
    """Кто вызвал MVC-action: HTTP-call, разобранные AuthArgs и текущая Session."""

    call: Call = None
    auth_args: AuthArgs = None
    session: Session = None
    lang: str = None
