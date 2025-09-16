import httpx
from pydantic import BaseModel
from rich.markup import escape


class AssertResult(BaseModel):
    success: bool
    reason: str | None

    @property
    def reason_escaped(self):
        return escape(self.reason) if self.reason else ""


class _AssertStatusCode(BaseModel):
    status_code: int | None = None

    def assert_status_code(self, response: httpx.Response) -> AssertResult:
        """checks if the status code is the same as the expected status code or just a success code"""

        if self.status_code:
            if response.status_code == self.status_code:
                return AssertResult(success=True, reason=None)
            else:
                return AssertResult(
                    success=False,
                    reason=f"Response status code was {response.status_code} expected {self.status_code}",
                )
        elif response.is_success:
            return AssertResult(success=True, reason="Response status code in 2xx")
        else:
            return AssertResult(success=False, reason="Response status code not in 2xx")


class _AssertTimeout(BaseModel):
    timeout_s: int | None = None
    """Will use httpx.USE_CLIENT_DEFAULT on the request setup if None"""


class AssertDef(_AssertStatusCode, _AssertTimeout):
    def check(self, response: httpx.Response) -> dict[str, AssertResult]:
        return {
            "status_code": self.assert_status_code(response),
            # "soft_timeout_s": _AssertTimeout.result(self, response),
        }
