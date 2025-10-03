from abc import ABCMeta, abstractmethod
import base64
from typing import override
from pydantic import BaseModel, SecretStr


class Auth(BaseModel, metaclass=ABCMeta):
    @property
    @abstractmethod
    def header(self) -> str: ...


class AuthBasic(Auth):
    username: str
    password: SecretStr

    @property
    @override
    def header(self):
        encoded = base64.b64encode(
            f"{self.username}:{self.password.get_secret_value()}".encode()
        ).decode()
        return f"Basic {encoded}"


class AuthBearerToken(Auth):
    token: str

    @property
    @override
    def header(self):
        return f"Bearer {self.token}"


class HasAuth(BaseModel):
    auth: AuthBasic | AuthBearerToken | None = None
    """
    A nicer way to generate Auth headers, overrides the requests headers under "Authorization:".
    """
