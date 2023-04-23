from dataclasses import dataclass
from typing import Optional, Any

from opyoid import PerLookupScope
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.controller import Controller
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException, \
    ERR_REASON_ACCESS_DENIED
from src.mybootstrap_mvc_itskovichanton.pipeline import Action
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter

from src.mybootstrap_pyauth_itskovichanton.entities import Caller
from src.mybootstrap_pyauth_itskovichanton.entities import Session
from src.mybootstrap_pyauth_itskovichanton.backend.session_storage import SessionStorage


@dataclass
class GetUserActionParams:
    session: Session
    fail_if_absent: bool = True


@bean(scope=PerLookupScope)
class GetUserAction(Action):
    session_storage: SessionStorage
    params: Optional[GetUserActionParams] = None

    def run(self, params: GetUserActionParams = None, prev_result: Any = None) -> Any:
        if not params:
            params = self.params
        r = self.session_storage.find_session(params.session)
        if not r and params.fail_if_absent:
            raise CoreException(message="Пользователь не существует", reason=ERR_REASON_ACCESS_DENIED)
        return r


@bean
class GetUserCountAction(Action):
    session_storage: SessionStorage

    def run(self, params: Any = None, prev_result: Any = None) -> Any:
        return self.session_storage.get_user_count()


@bean
class AuthController(Controller):
    default_result_presenter: ResultPresenter = default_dataclass_field(JSONResultPresenterImpl())
    get_user_action: GetUserAction
    get_user_count_action: GetUserCountAction

    async def get_user(self, caller: Caller):
        return await self.run(self.get_user_action)

    async def get_user_count(self, caller: Caller):
        return await self.run(self.get_user_count_action)
