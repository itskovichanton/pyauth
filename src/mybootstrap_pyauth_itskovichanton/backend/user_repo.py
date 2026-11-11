"""Репозиторий пользователей: контракт и in-memory реализация для тестов."""
from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from src.mybootstrap_pyauth_itskovichanton.entities import User


class UserRepo(Protocol):
    """Поиск и сохранение учётной записи. В сервисах обычно своя реализация поверх БД."""

    def put(self, a: User):
        ...

    def find(self, criteria: User) -> User:
        ...


@bean
class InMemUserRepo(UserRepo):
    """Словарь username → User. Подходит для тестов, не для нескольких процессов."""

    def __init__(self):
        self.storage = dict[str, User]()

    def put(self, a: User):
        """Записывает пользователя по username (пароль должен быть уже захэширован вызывающим)."""
        self.storage[a.username] = a

    def find(self, criteria: User) -> User:
        """Возвращает пользователя по username или None."""
        return self.storage.get(criteria.username)
