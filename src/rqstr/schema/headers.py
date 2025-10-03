from pydantic import BaseModel, Field, SecretStr


class HasHeaders(BaseModel):
    headers: dict[str, str] = Field(default_factory=dict)
    """Any headers to include in the request"""

    secret_headers: dict[str, SecretStr] = Field(default_factory=dict)
    """Any extra headers to include in the request, these will be removed on any output"""

    def all_headers(
        self, extra_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        if not extra_headers:
            extra_headers = {}

        return (
            self.headers
            | {k: v.get_secret_value() for k, v in self.secret_headers.items()}
            | extra_headers
        )
