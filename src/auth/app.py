from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean


@bean(no_polymorph=True)
class AuthApp(Application):
    server: AuthServer
    batch_service: DB

    def run(self):
        self.server.start()
