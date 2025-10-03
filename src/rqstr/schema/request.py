from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Annotated, Literal
import httpx
from loguru import logger
from piny import YamlStreamLoader
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    computed_field,
)
from typing_extensions import override

from rqstr.const import DEFAULT_OUT_DIR
from rqstr.schema.asserts import HasChecks
from rqstr.schema.auth import HasAuth
from rqstr.schema.headers import HasHeaders


class RequestData(HasHeaders, HasAuth, HasChecks):
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
    """The method to use when making the HTTP request"""

    url: AnyHttpUrl
    """The full url to use when sending the HTTP request"""

    query_params: dict[str, tuple[str, ...] | str | None] | None = None
    """
    Any query params to attach to the url. `k=v1,v2, ...` => `?k=v1&k=v2&...`.
    """

    body: dict[str, str] | None = None
    """The json bob to send as the body of the request"""

    benchmark: Annotated[int | None, Field(ge=0)] = None
    """The number of times to benchmark the request"""

    @override
    def __str__(self):
        return f"{self.method:<6} {self.to_httpx_request().url}"

    def to_httpx_request(
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

        return client.build_request(
            method=self.method,
            url=str(self.url),
            headers=self.all_headers(headers),
            params=self.query_params,
            json=self.body,
            timeout=self.check.timeout_s or httpx.USE_CLIENT_DEFAULT,
        )

    async def send_with(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str] | None = None,
    ) -> list[ResponseData]:
        """Makes a request and stores the result in the results list"""
        request = self.to_httpx_request(client, headers)
        logger.debug("Sending request {}", request)
        # todo, make async check for setup errors
        responses = await asyncio.gather(
            *(client.send(request) for _ in range(self.benchmark or 1))
        )
        return [
            ResponseData(
                method=self.method,
                url=self.url,
                query_params=self.query_params,
                body=self.body,
                benchmark=self.benchmark,
                headers=self.headers,
                secret_headers=self.secret_headers,
                auth=self.auth,
                check=self.check,
                response=r,
            )
            for r in responses
        ]


class OutputConf(BaseModel):
    enabled: bool = True
    output_dir: Path = Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))


class RequestCollection(HasHeaders, HasAuth):
    title: str
    description: str | None = None

    output: OutputConf = Field(default_factory=OutputConf)

    # todo, make a tree and exe in DAG, use stdlib graphlib
    requests: dict[str, RequestData] = Field(default_factory=dict)

    # todo features:
    # - output result to file
    # - benchmark with n requests

    async def collect(self):
        """Execute all requests in the collection."""
        async with httpx.AsyncClient(headers=self.headers) as client:
            # send each setup with the client and return the result
            _headers = self.all_headers()
            requests = {
                k: await v.send_with(client, headers=_headers)
                for k, v in self.requests.items()
            }
            return requests

    @classmethod
    def from_yml_file(cls, file: Path):
        yml = YamlStreamLoader(stream=file.read_text()).load()  # pyright: ignore [reportUnknownMemberType, reportAny]
        return RequestCollection.model_validate(yml)


class ResponseData(RequestData):
    response: httpx.Response
    """The httpx.Response that is received"""

    @property
    def httpx_request(self):
        return self.response.request

    @computed_field
    @property
    def status_code(self) -> int | None:
        return self.response.status_code

    @computed_field
    @property
    def response_text(self) -> str:
        return self.response.text

    @computed_field
    @property
    def is_success(self) -> bool:
        return self.response.is_success

    @override
    def __str__(self):
        return f"status {self.status_code} in {self.response.elapsed.total_seconds():.3f}s | success={self.is_success!r:<5} "

    model_config = {"arbitrary_types_allowed": True}
