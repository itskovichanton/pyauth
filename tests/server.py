import uvicorn
from fastapi import FastAPI
from src.mbulak_tools.log_compressor import LogCompressorImpl
from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.middleware_logging import HTTPLoggingMiddleware

from src.mybootstrap_pyauth_itskovichanton.frontend.support import AuthFastAPISupport


@bean(port=("server.port", int, 8000), host=("server.host", str, "0.0.0.0"))
class TestServer:
    auth_support: AuthFastAPISupport
    logger_service: LoggerService
    log_compressor: LogCompressorImpl

    def start(self):
        # self.logger_service.get_file_logger("http", formatter=CompressedHTTPLogFormatter("%(t)s %(msg)s",
        #                                                                               compressor=self.log_compressor))

        fast_api = FastAPI(title='Test', debug=False)
        fast_api.add_middleware(HTTPLoggingMiddleware,
                                encoding="utf-8",
                                logger=self.logger_service.get_file_logger("http"))

        self.auth_support.mount(fast_api)

        uvicorn.run(fast_api, port=self.port, host=self.host)
