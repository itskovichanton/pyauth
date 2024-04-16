from dataclasses import dataclass
from typing import Any

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException, \
    ERR_REASON_ACCESS_DENIED
from src.mybootstrap_mvc_itskovichanton.pipeline import Action, ActionRunner, Result

from src.mybootstrap_pyauth_itskovichanton.backend.auth import Authentificator
from src.mybootstrap_pyauth_itskovichanton.backend.session_storage import SessionStorage
from src.mybootstrap_pyauth_itskovichanton.entities import Caller, User, AuthArgs
from src.mybootstrap_pyauth_itskovichanton.entities import Session


@bean
class LoginAction(Action):
    auth: Authentificator

    def run(self, params: AuthArgs = None) -> Any:
        r = self.auth.login(params)
        r.account.password = None
        return r


@dataclass
class GetUserActionParams:
    session: Session
    token: str = None
    fail_if_absent: bool = True
    username: str = None


@bean
class GetUserAction(Action):
    session_storage: SessionStorage

    def run(self, params: Any = None) -> Any:

        if isinstance(params, User):
            return params

        if isinstance(params, Caller):
            params = params.session

        if isinstance(params, Session):
            params = GetUserActionParams(session=params)

        if isinstance(params, GetUserActionParams):
            if params.username:
                r = self.session_storage.find_session(Session(account=User(username=params.username)))
            else:
                if len(params.token or "") > 0:
                    r = self.session_storage.find_session(Session(token=params.token))
                else:
                    r = self.session_storage.find_session(params.session)
            if not r and params.fail_if_absent:
                raise CoreException(message="Пользователь не существует", reason=ERR_REASON_ACCESS_DENIED)
            return r

        raise CoreException(message="Невозможно определить пользователя", reason=ERR_REASON_ACCESS_DENIED)


@bean
class LogoutAllAction(Action):
    session_storage: SessionStorage

    def run(self, params: Any = None) -> Any:
        self.session_storage.logout_all()
        return "Все сессии очищены"


@bean
class GetUserToTokenStorageAction(Action):
    session_storage: SessionStorage

    def run(self, params: Any = None) -> Any:
        return self.session_storage.get_username_to_token_storage()


@bean
class GetTokenToSessionStorageAction(Action):
    session_storage: SessionStorage

    def run(self, params: Any = None) -> Any:
        return self.session_storage.get_token_to_session_storage()


class CheckCallerRoleAction(Action):

    def __init__(self, required_role: str, fail_msg: str = None):
        self.required_role = required_role
        self.fail_msg = fail_msg

    def run(self, params: Any = None) -> Any:
        passed_params = params

        if isinstance(params, Caller):
            params = params.session

        if isinstance(params, Session):
            params = params.account

        if not (params and params.role == self.required_role):
            raise CoreException(reason=ERR_REASON_ACCESS_DENIED, message=self.fail_msg)

        return passed_params


@bean
class AuthController:
    action_runner: ActionRunner
    get_user_action: GetUserAction
    get_user_to_token_action: GetUserToTokenStorageAction
    get_token_to_session_action: GetTokenToSessionStorageAction
    login_action: LoginAction
    logout_all_action: LogoutAllAction

    async def _execute_if_admin(self, action: Action, caller):
        return await self.action_runner.run(self.get_user_action,
                                            CheckCallerRoleAction(required_role="admin", fail_msg="Не достаточно прав"),
                                            action,
                                            call=caller)

    async def logout_all(self, caller: Caller) -> Result:
        return await self._execute_if_admin(action=self.logout_all_action, caller=caller)

    async def get_user(self, caller: Caller, username: str = None, token: str = None) -> Result:
        return await self._execute_if_admin(action=self.get_user_action,
                                            caller=GetUserActionParams(session=caller.session, username=username,
                                                                       token=token))

    async def get_user_to_token(self, caller: Caller) -> Result:
        return await self._execute_if_admin(action=self.get_user_action, caller=caller)

    async def get_token_to_session(self, caller: Caller) -> Result:
        return await self._execute_if_admin(self.get_token_to_session_action, caller=caller)

    async def login(self, auth_args: AuthArgs) -> Result:
        return await self.action_runner.run(self.login_action, call=auth_args)
