import uvicorn
from fastapi import FastAPI
from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.middleware_logging import HTTPLoggingMiddleware

from src.auth.frontend.controller import AuthController


@bean(port=("server.port", int, 8082), host=("server.host", str, "0.0.0.0"))
class AuthServer:
    controller: AuthController
    logger_service: LoggerService

    def init(self, **kwargs):
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        r = FastAPI(title='equifax-sync', debug=False)
        r.add_middleware(HTTPLoggingMiddleware, encoding="utf-8", logger=self.logger_service.get_file_logger("http"))
        return r

    def add_routes(self):
        @self.fast_api.get("/send-kh-daily")
        async def send_daily_batches(send: bool = True):
            return await self.controller.send_daily_batches(send=send)

        @self.fast_api.get("/check")
        async def check():
            return await self.controller.check()
