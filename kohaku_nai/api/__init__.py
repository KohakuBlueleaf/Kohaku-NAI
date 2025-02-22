import sys
import asyncio
from httpx import AsyncClient
from curl_cffi.requests import AsyncSession

from .image import (
    generate_novelai_image,
    DEFAULT_ARGS,
    QUALITY_TAGS,
    UCPRESET,
    MODEL_LIST
)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


API_URL = "https://api.novelai.net"
API_IMAGE_URL = "https://image.novelai.net"
HttpClient = AsyncClient | AsyncSession

jwt_token = ""
global_client: HttpClient | None = None


async def make_client(
    backend: str = "httpx",
    remote_server: str = "",
    password: str = "",
    token: str = "",
):
    assert backend in ["httpx", "curl_cffi"]
    assert remote_server or token
    if backend == "httpx":
        client_class = AsyncClient
    else:
        client_class = AsyncSession

    if remote_server:
        client = client_class(timeout=3600)
        payload = {"password": password}
        response = await client.post(f"{remote_server}/login", params=payload)
        if response.status_code == 200:
            return client, response.json()["status"]
    else:
        kwargs = {
            "timeout": 3600,
            "headers": {
                "Authorization": f"Bearer {token}",
            },
        }
        if backend == "curl_cffi":
            kwargs["impersonate"] = "chrome110"
        client = client_class(**kwargs)
        status = await client.get(f"{API_URL}/user/data")
        if status.status_code == 200:
            return client, status.json()
    return None, None


async def set_client(
    backend: str = "httpx",
    remote_server: str = "",
    password: str = "",
    token: str = "",
):
    global global_client
    global_client, status = await make_client(backend, remote_server, password, token)
    return status


__all__ = [
    "generate_novelai_image",
    "API_URL",
    "API_IMAGE_URL",
    "HttpClient",
    "jwt_token",
    "global_client",
    "set_client",
    "UCPRESET",
    "DEFAULT_ARGS",
    "QUALITY_TAGS",
    "MODEL_LIST",
]
