from abc import ABCMeta, abstractmethod
import asyncio
import base64
import statistics
from pydantic_core import from_json
from typing_extensions import override
from pathlib import Path
from typing import Literal

import httpx
from loguru import logger
from piny import YamlStreamLoader
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    PositiveFloat,
    PrivateAttr,
    SecretStr,
    computed_field,
)

from rqstr.response_checks import AssertDef

APP_NAME = "restaurant"
DEFAULT_OUT_DIR = f".{APP_NAME}/output"


class BaseResult(BaseModel):
    setup: "HttpSetup" = Field(exclude=True)
    model_config = {
        "arbitrary_types_allowed": True,
    }


class HttpResultError(BaseResult):
    request: httpx.Request = Field(exclude=True)
    error: httpx.RequestError | None = Field(default=None, exclude=True)


# specifies the recursive return type for parsed data
RtnDictTypes = int | float | None | str | bool
_RtnDict = dict[str, RtnDictTypes]
RtnDict = dict[str, _RtnDict | RtnDictTypes]


class HttpResult(BaseResult):
    response: httpx.Response = Field(exclude=True)

    @property
    def request(self):
        return self.response.request

    @property
    def tests(self):
        return self.setup.assert_

    @computed_field
    @property
    def status_code(self) -> int | None:
        return self.response.status_code

    @property
    def response_text(self) -> str:
        return self.response.text

    @property
    def parsed_response(self) -> RtnDict:
        try:
            return from_json(self.response_text, allow_partial=True)  # pyright: ignore [reportAny]
        except ValueError:
            return {}

    @computed_field
    @property
    def response_data(
        self,
    ) -> RtnDict | str:
        return self.parsed_response or self.response_text

    @computed_field
    @property
    def is_success(self) -> bool:
        return self.response.is_success

    @override
    def __str__(self):
        return f"status {self.status_code} in {self.response.elapsed.total_seconds():.3f}s | success={self.is_success!r:<5} "


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


class HttpSetup(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
    """The method to use when making the HTTP request"""

    url: AnyHttpUrl
    """The full url to use when sending the HTTP request"""

    extra_headers: dict[str, str] = Field(default_factory=dict)
    """Any extra headers to include in the request"""

    secret_headers: dict[str, SecretStr] = Field(default_factory=dict)
    """Any extra headers to include in the request, these will be removed on output"""

    query_params: dict[str, tuple[str, ...] | str | None] | None = None
    """
    Any query params to attach to the url.

    Multiple params with the same key will be added as multiple `k=v` entries.
    """

    auth: AuthBasic | AuthBearerToken | None = None
    """
    A nicer way to generate Auth headers, overrides the requests headers under "Authorization:".
    """

    body: dict[str, str] | None = None
    """The json bob to send as the body of the request"""

    assert_: AssertDef = Field(default_factory=AssertDef, alias="assert")
    """The tests to check responses against"""

    benchmark: int | None = Field(None, ge=0)
    """The number of times to benchmark the request"""

    _results: list[HttpResult | HttpResultError] = PrivateAttr(default_factory=list)

    @computed_field
    @property
    def results(self) -> list[HttpResult | HttpResultError]:
        return self._results

    @property
    def latest_result(self):
        return self.results[-1]

    @property
    def benchmark_min(self):
        return min(
            r.response.elapsed.total_seconds()
            for r in self.results
            if isinstance(r, HttpResult)
        )

    @property
    def benchmark_max(self):
        return max(
            r.response.elapsed.total_seconds()
            for r in self.results
            if isinstance(r, HttpResult)
        )

    @property
    def benchmark_mean(self):
        return statistics.mean(
            r.response.elapsed.total_seconds()
            for r in self.results
            if isinstance(r, HttpResult)
        )

    @property
    def benchmark_median(self):
        return statistics.median(
            r.response.elapsed.total_seconds()
            for r in self.results
            if isinstance(r, HttpResult)
        )

    @computed_field
    @property
    def benchmark_results(self) -> dict[str, PositiveFloat]:
        if self.benchmark:
            return {
                "count": len(self.results),
                "min": self.benchmark_min,
                "max": self.benchmark_max,
                "median": self.benchmark_median,
                "avg": self.benchmark_mean,
            }
        else:
            return {}

    @override
    def __str__(self):
        return f"{self.method:<6} {self._httpx_request().url}"

    def _httpx_request(
        self,
        client: httpx.AsyncClient | None = None,
        headers: dict[str, str] | None = None,
    ):
        if not client:
            logger.warning("client is required, making a temp one")
            client = httpx.AsyncClient()

        if not headers:
            headers = {}

        # generate auth header
        if self.auth:
            headers["Authorization"] = self.auth.header

        all_headers = (
            headers
            | self.extra_headers
            | {k: v.get_secret_value() for k, v in self.secret_headers.items()}
        )

        return client.build_request(
            method=self.method,
            url=str(self.url),
            headers=all_headers,
            params=self.query_params,
            json=self.body,
            timeout=self.assert_.timeout_s or httpx.USE_CLIENT_DEFAULT,
        )

    async def send_with(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str] | None = None,
    ):
        """Makes a request and stores the result in the results list"""
        request = self._httpx_request(client, headers)
        logger.debug("Sending request {}", request)
        # todo, make async check for setup errors
        responses = await asyncio.gather(
            *(client.send(request) for _ in range(self.benchmark or 1))
        )
        results = (HttpResult(setup=self, response=response) for response in responses)
        self._results.extend(results)
        return self


class RequestCollectionOutput(BaseModel):
    enabled: bool = True
    output_dir: Path = Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))


class RequestCollection(BaseModel):
    title: str
    description: str = ""
    headers: dict[str, str] = Field(default_factory=dict)
    """Global headers to include with each request"""

    # todo, make a tree and exe in DAG, use stdlib graphlib
    requests: dict[str, HttpSetup] = Field(default_factory=dict)

    # todo features:
    # - output result to file
    # - benchmark with n requests

    async def collect(self):
        """Execute all requests in the collection."""
        async with httpx.AsyncClient(headers=self.headers) as client:
            # send each setup with the client and return the result
            requests = {k: await v.send_with(client) for k, v in self.requests.items()}
            return requests

    @classmethod
    def from_yml_file(cls, file: Path):
        yml = YamlStreamLoader(stream=file.read_text()).load()  # pyright: ignore [reportUnknownMemberType, reportAny]
        return RequestCollection.model_validate(yml)


class GlobalConfig(BaseModel):
    output_dir: Path = Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))
