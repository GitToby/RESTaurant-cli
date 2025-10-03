import http
import httpx
import pytest
from http import HTTPStatus
from rqstr.schema.auth import AuthBasic
from rqstr.schema.request import RequestData, ResponseData


@pytest.fixture
def mock_client():
    return httpx.AsyncClient()


@pytest.fixture
def live_client():
    return httpx.AsyncClient()


@pytest.mark.asyncio
async def test__http_setup__init_raw(mock_client: httpx.AsyncClient):
    setup = RequestData(
        method="GET",
        url="https://postman-echo.com",  # pyright: ignore [reportArgumentType]
        query_params={"qp_1": ("a", "b", "c")},
    )
    req = setup.to_httpx_request(mock_client)
    assert isinstance(req, httpx.Request)
    assert req.method == "GET"
    assert req.url == httpx.URL("https://postman-echo.com/?qp_1=a&qp_1=b&qp_1=c")


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [200, 201, 404, 500])
async def test__live__http_setup__send_with_status_code(
    status_code: int, live_client: httpx.AsyncClient
):
    setup = RequestData(
        method="GET",
        url=f"https://postman-echo.com/status/{status_code}",  # pyright: ignore [reportArgumentType]
    )
    results = await setup.send_with(live_client)
    assert len(results) == 1
    assert isinstance(results[0], ResponseData)
    assert results[0].status_code == status_code
    assert results[0].is_success == http.HTTPStatus(status_code).is_success


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, password", [(200, "password"), (401, "wrong password")]
)
async def test__live__http_setup__send_with_basic_auth(
    live_client: httpx.AsyncClient, status_code: int, password: str
):
    # https://www.postman.com/postman/published-postman-templates/documentation/ae2ja6x/postman-echo?ctx=documentation&entity=request-42c867ca-e72b-3307-169b-26a478b00641
    username = "postman"

    setup = RequestData(
        method="GET",
        url="https://postman-echo.com/basic-auth",  # pyright: ignore [reportArgumentType]
        auth=AuthBasic(
            username=username,
            password=password,  # pyright: ignore[reportArgumentType]
        ),
    )
    assert setup.auth is not None
    results = await setup.send_with(live_client)
    assert len(results) == 1
    assert isinstance(results[0], ResponseData)
    assert results[0].status_code == status_code
    assert results[0].is_success == HTTPStatus(status_code).is_success


@pytest.mark.asyncio
async def test__live__http_setup__send_bad_request(live_client: httpx.AsyncClient):
    setup = RequestData(
        method="GET",
        url="https://this-really-shouldnt-be-a-domain.no-tld/",  # pyright: ignore [reportArgumentType]
    )

    with pytest.raises(httpx.ConnectError):
        _ = await setup.send_with(live_client)
