from dataclasses import dataclass
from typing import Optional, Any

from opyoid import PerLookupScope
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException, \
    ERR_REASON_ACCESS_DENIED
from src.mybootstrap_mvc_itskovichanton.pipeline import Action
from src.mybootstrap_pyauth_itskovichanton.entities import Session
from src.mybootstrap_pyauth_itskovichanton.session_storage import SessionStorage


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
