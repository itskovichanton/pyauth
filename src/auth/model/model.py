from dataclasses import dataclass
from typing import TypeVar, Generic

ID = TypeVar('ID')


@dataclass
class User(Generic[ID]):
    username: str
    password: str
    id: ID
