from restaurant.schema import AuthBasic, HttpResult, RequestCollection
from conftest import (  # pyright: ignore [reportImplicitRelativeImport]
    RESOURCES_DIR,
)
import os

import pytest


def test__request_collection__init_raw():
    collection = RequestCollection(title="Test Collection")
    assert collection.title == "Test Collection"
    assert len(collection.requests) == 0


@pytest.mark.asyncio
async def test__request_collection__init_file_secrets():
    os.environ["POSTMAN_PASSWORD"] = "password"

    collection = RequestCollection.from_yml_file(
        RESOURCES_DIR / "tests" / "secrets.rest.yml"
    )
    assert len(collection.requests) == 1

    http_basic = collection.requests["basic_env_var"]
    assert isinstance(http_basic.auth, AuthBasic)
    assert http_basic.auth.password.get_secret_value() == "password"

    results = await collection.collect()
    assert len(results) == 1
    assert isinstance(results[0], HttpResult)
    assert results[0].is_success
