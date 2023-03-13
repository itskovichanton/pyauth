from opyoid import Module
from src.mybootstrap_core_itskovichanton import di

from src.mybootstrap_mvc_itskovichanton.di import MVCModule


class AuthModule(Module):
    def configure(self) -> None:
        self.install(MVCModule)


injector = di.init([AuthModule])
