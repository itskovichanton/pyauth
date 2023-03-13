from src.auth.app import AuthApp
from src.auth.di import injector


def main() -> None:
    # alert_service = injector.inject(AlertService)
    # alert_service.get_interceptors().append(lambda e: None if isinstance(e,
    #                                                                      CoreException) and e.reason == ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND else e)
    app = injector.inject(AuthApp)
    app.run()


if __name__ == '__main__':
    main()
