from fastapi import FastAPI
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from starlette.requests import Request

from src.mybootstrap_pyauth_itskovichanton.frontend.controller import AuthController
from src.mybootstrap_pyauth_itskovichanton.frontend.utils import get_caller_from_request


@bean
class AuthFastAPISupport:
    controller: AuthController

    def mount(self, fast_api: FastAPI):
        @fast_api.get("/auth/getUser")
        async def get_user(request: Request):
            return await self.controller.get_user(caller=get_caller_from_request(request))

        @fast_api.get("/auth/getUserCount")
        async def get_user(request: Request):
            return await self.controller.get_user_count(caller=get_caller_from_request(request))
