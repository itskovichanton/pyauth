from src.mybootstrap_ioc_itskovichanton.di import injector

from app import AuthApp


def main() -> None:
    app = injector().inject(AuthApp)
    app.run()


if __name__ == '__main__':
    main()
