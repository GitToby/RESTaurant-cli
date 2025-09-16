import http
import httpx
from rqstr.schema import HttpResult, HttpResultError, HttpSetup
import pytest
import base64


@pytest.mark.asyncio
async def test__http_setup__init_raw():
    setup = HttpSetup(
        method="GET",
        url="https://postman-echo.com",  # pyright: ignore [reportArgumentType]
    )
    assert setup.results == []
    with pytest.raises(IndexError):
        setup.latest_result


@pytest.mark.asyncio
async def test__http_setup__init_from_file():
    setup = HttpSetup(
        method="GET",
        url="https://postman-echo.com",  # pyright: ignore [reportArgumentType]
    )
    assert setup.results == []
    with pytest.raises(IndexError):
        setup.latest_result


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [200, 201, 404, 500])
async def test__http_setup__send_with_status_code(status_code: int):
    setup = HttpSetup(
        method="GET",
        url=f"https://postman-echo.com/status/{status_code}",  # pyright: ignore [reportArgumentType]
    )
    test_client = httpx.AsyncClient()
    result = await setup.send_with(test_client)

    assert isinstance(result, HttpResult)
    assert result.status_code == status_code
    assert result.is_success == http.HTTPStatus(status_code).is_success


@pytest.mark.asyncio
async def test__http_setup__send_with_basic_auth_success():
    # https://www.postman.com/postman/published-postman-templates/documentation/ae2ja6x/postman-echo?ctx=documentation&entity=request-42c867ca-e72b-3307-169b-26a478b00641
    username = "postman"
    password = "password"
    encoded = base64.b64encode(f"{username}:{password}".encode()).decode()

    setup = HttpSetup(
        method="GET",
        url="https://postman-echo.com/basic-auth",  # pyright: ignore [reportArgumentType]
        extra_headers={
            # The Authorization request header contains the Base64-encoded username and password, seprated by a colon
            "Authorization": f"Basic {encoded}"
        },
    )
    test_client = httpx.AsyncClient()
    result = await setup.send_with(test_client)

    assert isinstance(result, HttpResult)
    assert result.is_success


@pytest.mark.asyncio
async def test__http_setup__send_with_basic_auth_failure():
    # https://www.postman.com/postman/published-postman-templates/documentation/ae2ja6x/postman-echo?ctx=documentation&entity=request-42c867ca-e72b-3307-169b-26a478b00641
    username = "postman"
    password = ""
    encoded = base64.b64encode(f"{username}:{password}".encode()).decode()

    setup = HttpSetup(
        method="GET",
        url="https://postman-echo.com/basic-auth",  # pyright: ignore [reportArgumentType]
        extra_headers={
            # The Authorization request header contains the Base64-encoded username and password, seprated by a colon
            "Authorization": f"Basic {encoded}"
        },
    )
    test_client = httpx.AsyncClient()
    result = await setup.send_with(test_client)

    assert isinstance(result, HttpResult)
    assert not result.is_success
    assert result.response.text == "Unauthorized"


@pytest.mark.asyncio
async def test__http_setup__send_bad_request():
    setup = HttpSetup(
        method="GET",
        url="https://this-really-shouldnt-be-a-domain.no-tld/",  # pyright: ignore [reportArgumentType]
    )
    test_client = httpx.AsyncClient()
    result = await setup.send_with(test_client)

    assert isinstance(result, HttpResultError)
