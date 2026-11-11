"""
Хранилище пользовательских сессий.

Это критичный модуль авторизации: он решает, какой токен считать валидным входом
и какой ``User`` к нему привязан.

Две коллекции в Redis (через :meth:`RedisService.make_map`):

* ``token → Session`` — поиск сессии по заголовку ``sessionToken``.
* ``slug+username → token`` — не больше одной активной сессии на пользователя:
  повторный логин инвалидирует предыдущий токен.

Безопасность:

* токен — ``secrets.token_urlsafe``, не MD5;
* в Redis не кладётся ``User.password`` (даже хэш);
* ``logout_all`` чистит только эти две map, а не весь Redis (``FLUSHDB`` недопустим);
* у сессии есть TTL (``auth.session_ttl_sec``, по умолчанию 7 суток).
"""
from __future__ import annotations

import secrets
import threading
from copy import deepcopy
from dataclasses import dataclass, is_dataclass
from typing import Callable, Protocol

import dacite
from src.mbulak_tools.events import event_bus
from src.mybootstrap_core_itskovichanton.redis_service import RedisService
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from src.mybootstrap_pyauth_itskovichanton.entities import Session, User

EVENT_LOGOUT = "event-logout"
EVENT_LOGIN = "event-login"

# Минимальная длина принудительно заданного токена (тесты / регистрация).
_MIN_FORCED_TOKEN_LEN = 16
_DEFAULT_SESSION_TTL_SEC = 7 * 24 * 3600
_TOKEN_BYTES = 32


@dataclass
class _TokenRef:
    """Значение map «пользователь → токен» (make_map требует класс, не сырой str)."""

    token: str = ""


class TokenFactory(Protocol):
    """Генератор непрозрачных session-токенов."""

    def generate(self, token_to_fix: str, user: User) -> str:
        ...


@bean
class SimpleTokenFactory(TokenFactory):
    """Криптостойкий токен (url-safe, ~256 бит). Параметры оставлены для совместимости протокола."""

    def generate(self, token_to_fix: str, user: User) -> str:
        return secrets.token_urlsafe(_TOKEN_BYTES)


class SessionStorage(Protocol):
    """Контракт хранилища сессий (поиск, вход, выход, дамп для админки)."""

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

    def update_session(self, token: str, updater: Callable[[Session], None]) -> Session:
        ...


def _username_key(user: User) -> str:
    """Стабильный ключ пользователя внутри Redis (slug + username)."""
    if user is None:
        return ""
    return f"slug={user.slug or ''}::username={user.username or ''}"


def _without_password(user: User | None) -> User | None:
    """Копия пользователя без поля password — его нельзя держать в сессионном Redis."""
    if user is None:
        return None
    clone = deepcopy(user)
    clone.password = None
    return clone


@bean(session_ttl_sec=("auth.session_ttl_sec", int, _DEFAULT_SESSION_TTL_SEC))
class RedisSessionStorage(SessionStorage):
    """
    Redis-реализация :class:`SessionStorage`.

    Hash-имена: ``{app_name}:auth:sessions`` и ``{app_name}:auth:user_tokens``.
    """

    token_factory: TokenFactory
    config_service: ConfigService
    redis_service: RedisService

    def init(self):
        self.lock = threading.Lock()
        self._user_class = User
        self._ttl = self.session_ttl_sec if self.session_ttl_sec and self.session_ttl_sec > 0 else None
        self._build_maps()

    def _build_maps(self):
        self.token_to_session = self.redis_service.make_map(
            Session,
            hname="auth:sessions",
            key_prefix="ts",
            deserializer=self._deserialize_session,
            pre_serializer=self._prepare_session,
        )
        self.username_to_token = self.redis_service.make_map(
            _TokenRef,
            hname="auth:user_tokens",
            key_prefix="ut",
        )

    def _prepare_session(self, session: Session) -> Session:
        if session is None:
            return session
        return Session(token=session.token, account=_without_password(session.account))

    def _deserialize_session(self, _value_class, value_dict: dict) -> Session:
        account_raw = (value_dict or {}).get("account")
        account = None
        if isinstance(account_raw, dict):
            account_raw = {k: v for k, v in account_raw.items() if k != "password"}
            account = dacite.from_dict(
                data_class=self._user_class,
                data=account_raw,
                config=dacite.Config(strict=False, check_types=False),
            )
        elif is_dataclass(account_raw) and account_raw is not None:
            account = _without_password(account_raw)
        return Session(token=(value_dict or {}).get("token"), account=account)

    def set_user_class(self, user_class=User):
        """Подменяет класс ``account`` (наследник ``User`` в конкретных сервисах)."""
        self._user_class = user_class or User

    def find_session(self, criteria: Session) -> Session | None:
        """Ищет сессию по токену или по username/slug аккаунта. Битые ссылки username→token чистятся."""
        if not criteria:
            return None

        if criteria.token:
            return self.token_to_session.get(criteria.token)

        if not criteria.account:
            return None

        ref = self.username_to_token.get(_username_key(criteria.account))
        token = ref.token if ref else None
        if not token:
            return None

        session = self.token_to_session.get(token)
        if session:
            return session
        self.username_to_token.delete(_username_key(criteria.account))
        return None

    def logout(self, criteria: Session) -> Session | None:
        """Удаляет сессию по токену или пользователю и шлёт ``EVENT_LOGOUT``."""
        removed_session = self.find_session(criteria)
        if not removed_session:
            return None

        with self.lock:
            self.token_to_session.delete(removed_session.token)
            if removed_session.account:
                self.username_to_token.delete(_username_key(removed_session.account))
            event_bus.emit(EVENT_LOGOUT, session=removed_session)
        return removed_session

    def logout_all(self):
        """Сбрасывает только сессии этого приложения, не всю Redis-базу."""
        with self.lock:
            self.token_to_session.clear()
            self.username_to_token.clear()

    def assign_session(self, user: User, forced_session_token: str = None) -> Session:
        """
        Создаёт новую сессию: старая для этого пользователя закрывается.

        ``forced_session_token`` — только для тестов/миграций, должен быть достаточно длинным.
        """
        if user is None or not user.username:
            raise CoreException(message="Нельзя выдать сессию без username")

        if forced_session_token is not None:
            if len(forced_session_token) < _MIN_FORCED_TOKEN_LEN:
                raise CoreException(
                    message=f"Принудительный токен короче {_MIN_FORCED_TOKEN_LEN} символов",
                )

        self.logout(Session(account=user, token=forced_session_token))

        with self.lock:
            new_token = forced_session_token or self._calc_new_token(user)
            session = Session(token=new_token, account=_without_password(user))

            self.username_to_token.set(_username_key(user), _TokenRef(token=new_token), ttl=self._ttl)
            self.token_to_session.set(new_token, session, ttl=self._ttl)
            event_bus.emit(EVENT_LOGIN, session=session)

        return session

    def _calc_new_token(self, user: User) -> str:
        """Генерирует токен, которого ещё нет в ``token_to_session`` (коллизии практически невозможны)."""
        token = self.token_factory.generate(user.slug or "", user)
        while self.token_to_session.get(token):
            token = self.token_factory.generate(token, user)
        return token

    def update_session(self, token: str, updater: Callable[[Session], None]) -> Session:
        """Атомарно (под lock) меняет поля существующей сессии, пароль снова вычищается."""
        if not token:
            return None
        with self.lock:
            session = self.token_to_session.get(token)
            if session is None:
                return None
            updater(session)
            session.account = _without_password(session.account)
            self.token_to_session.set(token, session, ttl=self._ttl)
            return session

    def get_token_to_session_storage(self) -> dict:
        """Дамп token→session для админки (паролей в значениях быть не должно)."""
        return self.token_to_session.get_all()

    def get_username_to_token_storage(self) -> dict:
        """Дамп username→token для админки."""
        raw = self.username_to_token.get_all()
        return {k: v.token for k, v in raw.items()}
