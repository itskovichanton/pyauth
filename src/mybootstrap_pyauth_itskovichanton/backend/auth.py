from typing import Protocol

from src.mybootstrap_core_itskovichanton import validation
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from src.mybootstrap_pyauth_itskovichanton.backend.session_storage import SessionStorage
from src.mybootstrap_pyauth_itskovichanton.backend.user_repo import UserRepo
from src.mybootstrap_pyauth_itskovichanton.entities import User, Session, AuthArgs


class PasswordValidator(Protocol):
    def password_are_matched(self, passed, correct) -> bool:
        ...


@bean
class StraightPasswordValidator(PasswordValidator):
    def password_are_matched(self, passed, correct) -> bool:
        return passed == correct


class Authentificator(Protocol):

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
    user_repo: UserRepo
    session_storage: SessionStorage
    password_validator: PasswordValidator

    def logout_all(self):
        self.session_storage.logout_all()

    def logout(self, session: Session) -> Session:
        return self.session_storage.logout(session)

    def login(self, a: AuthArgs) -> Session:

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

        validation.check_not_empty("username", a.username)
        validation.check_not_empty("password", a.password)

        a = self.user_repo.find(a)
        if a and not idempotent:
            raise CoreException(message=f"Пользователь с именем {a.username} уже существует",
                                reason=REASON_USER_ALREADY_EXISTS)

        self.user_repo.put(a)

        return self.session_storage.assign_session(a, forced_session_token=session_token)
