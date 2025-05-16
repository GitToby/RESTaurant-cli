import asyncio
from http import HTTPStatus
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, AnyHttpUrl, Field
import httpx
from piny import YamlStreamLoader

APP_NAME = "restaurant"
DEFAULT_OUT_DIR = f".{APP_NAME}/output"


class HttpRequestCheckStatusCode(BaseModel):
    status_code: int | None = None

    def check_status_code(self, response: httpx.Response) -> bool:
        """checks if the status code is the same as the expected status code or just a success code"""
        if self.status_code:
            return response.status_code == self.status_code
        else:
            return HTTPStatus(response.status_code).is_success


class HttpRequestCheckTimeout(BaseModel):
    soft_timeout_s: float | None = None

    def check_timeout(self, response: httpx.Response) -> bool:
        """checks if the response time is less than the expected timeout"""
        if self.soft_timeout_s:
            return response.elapsed.total_seconds() <= self.soft_timeout_s
        else:
            return True


class HttpRequestCheck(HttpRequestCheckStatusCode, HttpRequestCheckTimeout):
    def check(self, response: httpx.Response) -> bool:
        """checks if the response is valid"""
        return self.check_status_code(response) and self.check_timeout(response)


class HttpSetup(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
    url: AnyHttpUrl
    extra_headers: dict[str, str] = Field(default_factory=dict)
    query_params: tuple[tuple[str, str], ...] | None = None
    body: dict[str, str] | None = None

    test: HttpRequestCheck = Field(default_factory=HttpRequestCheck, alias="assert")

    # def __hash__(self) -> int:
    # return hash(self.method + self.url)

    async def make_request(self, client: httpx.AsyncClient):
        try:
            response = await client.request(
                method=self.method,
                url=str(self.url),
                headers=self.extra_headers,
                params=self.query_params,
                json=self.body,
            )
            # print(response.request.headers)
            return Result(
                setup=self,
                response=response,
            )
        except httpx.RequestError as e:
            return Result(setup=self, response=e)


# class ResultData(BaseModel):
#     success: bool
#     request: ...# req settings
#     response: ...# resp settings


# todo, make json serializable with a to_str for logging
class Result(BaseModel):
    setup: "HttpSetup"
    response: httpx.Response | httpx.RequestError

    model_config = {
        "arbitrary_types_allowed": True,
    }

    @property
    def was_success(self):
        if isinstance(self.response, httpx.RequestError):
            return False
        return self.setup.test.check(self.response)

    @property
    def pretty_str(self) -> str:
        success_emoji = "✅"
        if isinstance(self.response, httpx.RequestError):
            status_str = f"[red]Error {str(self.response)}[/red]"
            time_str = "()"
            success_emoji = "❌"
        else:
            status_str = self.response.history
            status_str = f"[green]{self.response.status_code}[/green]"
            time_str = f"({self.response.elapsed})"

            if not self.setup.test.check_status_code(self.response):
                status_str = f"[red]{self.response.status_code}[/red] expected [purple]{self.setup.test.status_code or '2xx'}[/purple] "
                success_emoji = "❌"

            if not self.setup.test.check_timeout(self.response):
                time_str = f"[red]({self.response.elapsed})[/red] expected < [purple]{self.setup.test.soft_timeout_s}[/purple]"
                success_emoji = "❌"

        return f"{success_emoji} {self.setup.method:<8} {self.response.request.url} {status_str} {time_str}"


class RequestCollectionOutput(BaseModel):
    enabled: bool = True
    output_dir: Path = Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))


# todo, load from yml file
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
        return [request.make_request(client) for request in self.requests.values()]

    async def execute(self):
        """Execute all requests in the collection."""
        async with httpx.AsyncClient(headers=self.headers) as client:
            requests = self.collect(client)
            results = await asyncio.gather(*requests)
            return results

    @classmethod
    def load_from_file(cls, file: Path):
        yml = YamlStreamLoader(stream=file.read_text()).load()
        return RequestCollection.model_validate(yml)


class GlobalConfig(BaseModel):
    output_dir: Path = Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))
