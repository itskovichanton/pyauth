"""
Сценарии входа, регистрации и выхода.

Пароль сверяется через :class:`PasswordValidator` (Argon2 по умолчанию).
Сессия после успешного входа выдаётся :class:`SessionStorage`.
"""
from typing import Protocol

from argon2 import PasswordHasher
from src.mybootstrap_core_itskovichanton import validation
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from src.mybootstrap_pyauth_itskovichanton.backend.session_storage import SessionStorage
from src.mybootstrap_pyauth_itskovichanton.backend.user_repo import UserRepo
from src.mybootstrap_pyauth_itskovichanton.entities import AuthArgs, Session, User


class PasswordValidator(Protocol):
    """Сравнение пароля с сохранённым секретом и генерация хэша при регистрации."""

    def password_are_matched(self, passed, correct) -> bool:
        ...

    def generate_hash(self, password: str) -> str:
        ...


@bean
class Argon2PasswordValidator(PasswordValidator):
    """Проверка пароля по хэшу Argon2 (рекомендуемый вариант для продакшена)."""

    def init(self) -> None:
        self._hasher = PasswordHasher()

    def generate_hash(self, password: str) -> str:
        """Хэш для сохранения в репозитории пользователей."""
        return self._hasher.hash(password)

    def password_are_matched(self, passed: str, correct: str) -> bool:
        """
        Сверяет открытый пароль с хэшем из БД.

        :param passed: пароль, введённый пользователем.
        :param correct: строка Argon2 из хранилища.
        """
        try:
            return self._hasher.verify(correct, passed)
        except BaseException:
            return False


@bean
class StraightPasswordValidator(PasswordValidator):
    """Сравнение паролей как есть. Только для тестов и локальной разработки, не для продакшена."""

    def password_are_matched(self, passed, correct) -> bool:
        return passed == correct

    def generate_hash(self, password: str) -> str:
        return password


class Authentificator(Protocol):
    """Фасад регистрации / login / logout поверх UserRepo + SessionStorage."""

    def register(self, a: User, session_token: str = None, idempotent=False) -> Session:
        ...

    def login(self, auth_args: AuthArgs) -> Session:
        ...

    def logout(self, session: Session) -> Session:
        ...

    def logout_all(self):
        ...


REASON_USER_ALREADY_EXISTS = "REASON_ALREADY_EXIST"
REASON_INVALID_PASSWORD = "REASON_AUTHORIZATION_FAILED_INVALID_PASSWORD"
REASON_USER_NOT_EXISTS = "REASON_AUTHORIZATION_FAILED_USER_NOT_EXIST"
REASON_EMPTY_CREDS = "REASON_EMPTY_CREDS"


@bean
class AuthentificatorImpl(Authentificator):
    """Стандартная реализация: пользователи в UserRepo, сессии в SessionStorage."""

    user_repo: UserRepo
    session_storage: SessionStorage
    password_validator: PasswordValidator

    def logout_all(self):
        """Инвалидирует все сессии приложения (не Redis целиком)."""
        self.session_storage.logout_all()

    def logout(self, session: Session) -> Session:
        """Выход одной сессии по токену или пользователю."""
        return self.session_storage.logout(session)

    def login(self, a: AuthArgs) -> Session:
        """
        Вход по sessionToken или по username+password.

        Существующий токен не продлевает сессию сам по себе — TTL задаётся при assign_session.
        """
        if not a:
            raise CoreException(message="Нет данных для входа", reason=REASON_EMPTY_CREDS)

        if len(a.session_token or "") > 0:
            r = self.session_storage.find_session(Session(token=a.session_token))
            if r:
                return r

        validation.check_not_empty("username", a.username)
        validation.check_not_empty("password", a.password)

        user = self.user_repo.find(User(username=a.username))
        if not user:
            raise CoreException(message=f"Пользователь с именем {a.username} не существует",
                                reason=REASON_USER_NOT_EXISTS)

        if not self.password_validator.password_are_matched(a.password, user.password):
            raise CoreException(message="Неверный пароль", reason=REASON_INVALID_PASSWORD)

        return self.session_storage.assign_session(user)

    def register(self, a: User, session_token: str = None, idempotent=False) -> Session:
        """Создаёт пользователя (или переиспользует при idempotent) и сразу выдаёт сессию."""
        validation.check_not_empty("username", a.username)
        validation.check_not_empty("password", a.password)

        existing = self.user_repo.find(a)
        if existing and not idempotent:
            raise CoreException(message=f"Пользователь с именем {a.username} уже существует",
                                reason=REASON_USER_ALREADY_EXISTS)
        if existing:
            a = existing
        self.user_repo.put(a)

        return self.session_storage.assign_session(a, forced_session_token=session_token)
