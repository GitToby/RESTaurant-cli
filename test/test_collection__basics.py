from conftest import (  # pyright: ignore [reportImplicitRelativeImport]
    RESOURCES_DIR,
)

import pytest

from rqstr.schema.auth import AuthBasic
from rqstr.schema.request import RequestCollection


def test__request_collection__init_raw():
    collection = RequestCollection(title="Test Collection")
    assert collection.title == "Test Collection"
    assert len(collection.requests) == 0


@pytest.mark.asyncio
async def test__request_collection__init_file_secrets(monkeypatch: pytest.MonkeyPatch):
    pw_value = "my_password"
    monkeypatch.setenv("POSTMAN_PASSWORD", pw_value)

    collection = RequestCollection.from_yml_file(RESOURCES_DIR / "secrets.rest.yml")
    assert len(collection.requests) == 2

    http_basic = collection.requests["basic env var"]
    assert isinstance(http_basic.auth, AuthBasic)
    assert http_basic.auth.password.get_secret_value() == pw_value
    
    defaults_not_set = collection.requests["defaults and not set"]
    assert defaults_not_set.query_params
    assert len(defaults_not_set.query_params) == 2
    assert defaults_not_set.query_params["default_val"] == "12"
    assert defaults_not_set.query_params["not_set"] is None

