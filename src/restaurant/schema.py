from abc import abstractmethod
import base64
from typing_extensions import override
import asyncio
from functools import cached_property
from pathlib import Path
from typing import Literal

import httpx
from loguru import logger
from piny import YamlStreamLoader
from pydantic import AnyHttpUrl, BaseModel, Field, PrivateAttr, SecretStr
from pydantic.fields import computed_field

from restaurant.response_checks import AssertDef

APP_NAME = "restaurant"
DEFAULT_OUT_DIR = f".{APP_NAME}/output"


class HttpResultError(BaseModel):
    request: httpx.Request = Field(exclude=True)
    error: httpx.RequestError | None = Field(default=None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True,
    }


class HttpResult(BaseModel):
    response: httpx.Response = Field(exclude=True)
    tests: AssertDef | None = Field(default=None, exclude=True)

    @property
    def request(self):
        return self.response.request

    @computed_field
    @property
    def status_code(self) -> int | None:
        return self.response.status_code

    @computed_field
    @cached_property
    def response_text(self) -> str | None:
        return self.response.text

    @computed_field
    @property
    def is_success(self) -> bool:
        return self.response.is_success

    model_config = {
        "arbitrary_types_allowed": True,
    }


class Auth(BaseModel):
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


class HttpSetup(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
    """The method to use when making the HTTP request"""

    url: AnyHttpUrl
    """The full url to use when sending the HTTP request"""

    extra_headers: dict[str, str] = Field(default_factory=dict)
    """Any extra headers to include in the request"""

    query_params: dict[str, tuple[str, ...] | str | None] | None = None
    """
    Any query params to attach to the url.

    Multiple params with the same key will be added as multiple `k=v` entries.
    """

    auth: AuthBasic | AuthBearerToken | None = None
    """
    A nicer way to generate Auth headers
    """

    body: dict[str, str] | None = None
    """The json bob to send as the body of the request"""

    assert_: AssertDef = Field(default_factory=AssertDef, alias="assert")
    """The tests to check responses against"""

    _results: list[HttpResult] = PrivateAttr(default_factory=list)
    _errors: list[HttpResultError] = PrivateAttr(default_factory=list)

    @property
    def results(self):
        return self._results

    @property
    def latest_result(self) -> HttpResult:
        return self.results[-1]

    async def send_with(self, client: httpx.AsyncClient):
        # generate auth header
        if self.auth:
            self.extra_headers["Authorization"] = self.auth.header

        request = client.build_request(
            method=self.method,
            url=str(self.url),
            headers=self.extra_headers,
            params=self.query_params,
            json=self.body,
            timeout=self.assert_.timeout_s or httpx.USE_CLIENT_DEFAULT,
        )
        try:
            logger.debug("Sending request {}", self)
            response = await client.send(request)
            result = HttpResult(response=response, tests=self.assert_)
            self._results.append(result)
        except httpx.RequestError as e:
            logger.warning("Error with request {}", e)
            result = HttpResultError(request=request, error=e)
            self._errors.append(result)

        return result


class RequestCollectionOutput(BaseModel):
    enabled: bool = True
    output_dir: Path = Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))


class RequestCollection(BaseModel):
    title: str
    description: str = ""
    headers: dict[str, str] = Field(default_factory=dict)

    # todo, make a tree and exe in DAG, use stdlib graphlib
    requests: dict[str, HttpSetup] = Field(default_factory=dict)

    # todo features:
    # - output result to file
    # - benchmark with n requests
    # - read secrets from env vars/secret store

    def collect(self, client: httpx.AsyncClient):
        """Collect all requests as async httpx requests."""
        return [request.send_with(client) for request in self.requests.values()]

    async def execute(self):
        """Execute all requests in the collection."""
        async with httpx.AsyncClient(headers=self.headers) as client:
            requests = self.collect(client)
            results = await asyncio.gather(*requests)
            return results

    @classmethod
    def from_yml_file(cls, file: Path):
        yml = YamlStreamLoader(stream=file.read_text()).load()
        return RequestCollection.model_validate(yml)


class GlobalConfig(BaseModel):
    output_dir: Path = Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))
