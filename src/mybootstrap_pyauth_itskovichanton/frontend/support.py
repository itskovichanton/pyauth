from fastapi import FastAPI
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter
from starlette.requests import Request

from src.mybootstrap_pyauth_itskovichanton.frontend.controller import AuthController
from src.mybootstrap_pyauth_itskovichanton.frontend.utils import get_caller_from_request


@bean
class AuthFastAPISupport:
    controller: AuthController
    presenter: ResultPresenter = default_dataclass_field(JSONResultPresenterImpl(exclude_none=True))

    def mount(self, fast_api: FastAPI):
        @fast_api.get("/auth/logoutAll")
        async def logout(request: Request):
            return self.presenter.present(await self.controller.logout_all(caller=get_caller_from_request(request)))

        @fast_api.get("/auth/getUser")
        async def get_user(request: Request, username: str = None, token: str = None):
            return self.presenter.present(
                await self.controller.get_user(caller=get_caller_from_request(request), username=username, token=token))

        @fast_api.get("/auth/getUserToToken")
        async def get_user_to_token(request: Request):
            return self.presenter.present(
                await self.controller.get_user_to_token(caller=get_caller_from_request(request)))

        @fast_api.get("/auth/getTokenToSession")
        async def get_token_to_session(request: Request):
            return self.presenter.present(
                await self.controller.get_token_to_session(caller=get_caller_from_request(request)))

        @fast_api.get("/auth/login")
        async def login(request: Request):
            return self.presenter.present(
                await self.controller.login(auth_args=get_caller_from_request(request).auth_args))
