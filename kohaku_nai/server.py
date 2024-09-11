import asyncio
import os
import re
import json
import time
import random
import click
import heapq
from uvicorn import Config, Server
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from hashlib import sha3_256

import toml
from snowflake import SnowflakeGenerator

from fastapi import FastAPI, Request, Response
from starlette.middleware.sessions import SessionMiddleware

from kohaku_nai.utils import (
    generate_novelai_image,
    free_check,
    make_client,
    image_from_bytes,
    process_image_as_webp,
    HttpClient,
)
from kohaku_nai.request import GenerateRequest
from kohaku_nai.config_spec import GenServerConfig


id_gen = SnowflakeGenerator(1)

server_config: None | GenServerConfig = None
auth_configs: list[GenServerConfig] = []
nai_clients: dict[str, "NAILocalClient"] = {}
retry_list: set[int] = set()
prev_gen_time = time.time()
priority_queue = []

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=uuid4().hex)

generate_semaphore: None | asyncio.Semaphore = None
save_worker = ThreadPoolExecutor(16)


class NAILocalClient:
    def __init__(self, token, client: HttpClient):
        self.token = token
        self.client = client
        self.error_time = 0
        self.in_error = False
        self.lock = asyncio.Lock()

    @classmethod
    async def create(cls, token):
        client, status = await make_client(
            server_config.get("http_backend", "curl_cffi"), token=token
        )
        if status is None:
            return None
        return cls(token, client)

    @property
    def available(self):
        return not self.lock.locked()

    async def disable(self):
        await self.lock.acquire()

    def enable(self):
        self.lock.release()

    async def __aenter__(self) -> HttpClient:
        await self.lock.acquire()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.enable()


def save_img(save_path: str, sub_folder: str, image: bytes, json: str):
    if not save_path:
        save_path = server_config["save_path"]
    sub_folder_path = os.path.join(save_path, sub_folder)
    os.makedirs(sub_folder_path, exist_ok=True)
    is_separate_metadata = server_config.get("separate_metadata", False)
    metadata_dir = "metadatas"
    if is_separate_metadata:
        os.makedirs(os.path.join(sub_folder_path, metadata_dir), exist_ok=True)

    img_hash = sha3_256(image).hexdigest()
    img_id = next(id_gen)
    img_extension = "png" if server_config.get("save_directly", False) else "webp"
    img_name = f"{img_id}_{img_hash[:8]}.{img_extension}"

    with open(os.path.join(sub_folder_path, img_name), "wb") as f:
        f.write(image)
    if is_separate_metadata:
        metadata_name = f"{img_id}_{img_hash[:8]}.json"
        with open(
            os.path.join(sub_folder, metadata_dir, metadata_name), "w", encoding="utf-8"
        ) as f:
            f.write(json)


@app.post("/login")
async def login(password: str, request: Request):
    for auth in auth_configs:
        if password == auth["password"]:
            request.session["signed"] = True
            request.session["free_only"] = auth.get("free_only", True)
            request.session["save_path"] = auth.get(
                "save_path", server_config["save_path"]
            )
            request.session["custom_sub_folder"] = auth.get("custom_sub_folder", False)
            request.session["max_priority"] = auth.get("max_priority", 1)
            return {"status": "login success"}
    else:
        request.session.clear()
        return Response(json.dumps({"status": "login failed"}), 403)


async def get_available_client(priority: int = 0) -> NAILocalClient:
    global priority_queue
    request_time = time.time()
    priority_info = (-priority, request_time)
    heapq.heappush(priority_queue, priority_info)
    while True:
        if priority_queue[0] is not priority_info:
            await asyncio.sleep(0)
            continue
        for client in nai_clients.values():
            if client is None:
                continue
            if not client.available:
                # Not available
                continue
            elif not client.in_error:
                # available + no error
                break
            elif time.time() >= client.error_time + server_config["retry_delay"]:
                # available + in error + retry delay passed
                client.in_error = False
                break
            else:
                # in error + retry delay not passed
                # Use asyncio.sleep to yield control to the event loop
                await asyncio.sleep(0)
                continue
        else:
            # No client available
            # Use asyncio.sleep to yield control to the event loop
            await asyncio.sleep(0)
            continue
        heapq.heappop(priority_queue)
        break
    return client


def make_error(error_mes, response, retry_count):
    try:
        error_response = response.json()
        if (
            "statusCode" in error_response
            and (status_code := error_response["statusCode"]) in retry_list
        ):
            if retry_count >= server_config["max_retries"]:
                print(f"Exceed max retries for NAI {status_code} errors: {error_mes}")
                return Response(
                    json.dumps(
                        {
                            "error-mes": "Exceed max retries for NAI errors",
                            "status": f"{status_code} error from NAI server",
                        }
                    ),
                    500,
                )
            return None
    except json.JSONDecodeError:
        error_response = response.text
    return Response(json.dumps({"error-mes": error_mes, "status": error_response}), 500)


@app.post("/gen")
async def gen(context: GenerateRequest, request: Request):
    global prev_gen_time

    is_signed = request.session.get("signed", False)
    is_free_only = request.session.get("free_only", True)
    # no max_priority means the user is not login
    max_priority = request.session.get("max_priority", 0)
    priority = min(max_priority, context.priority)
    try:
        extra_infos = json.loads(context.extra_infos)
    except json.JSONDecodeError:
        return Response(
            json.dumps(
                {"status": "Extra infos in invalid format, please send json strings."}
            ),
            403,
        )
    is_always_require_auth = server_config.get("always_require_auth", True)
    is_free_gen = free_check(context.width, context.height, context.steps)

    save_path = request.session.get("save_path", server_config["save_path"])
    if request.session.get("custom_sub_folder", False):
        sub_folder = context.img_sub_folder or extra_infos.get("save_folder", "")
    else:
        sub_folder = ""
    safe_folder_name = re.sub(r"[^\w\-_\. ]", "_", sub_folder)

    if (not is_signed and (is_always_require_auth or not is_free_gen)) or (
        is_free_only and not is_free_gen
    ):
        return Response(json.dumps({"status": "Config not allowed"}), 403)

    retry_count = 0
    while True:
        client = await get_available_client(priority)
        async with client as http_client:
            async with generate_semaphore:
                if prev_gen_time + server_config["min_delay"] > time.time():
                    await asyncio.sleep(
                        server_config["min_delay"] + random.random() * 0.3
                    )
                prev_gen_time = time.time()

                img_bytes, json_payload = await generate_novelai_image(
                    context.prompt,
                    False,
                    context.neg_prompt,
                    "",
                    context.seed,
                    context.scale,
                    context.width,
                    context.height,
                    context.steps,
                    context.sampler,
                    context.schedule,
                    context.smea,
                    context.dyn,
                    context.dyn_threshold,
                    context.cfg_rescale,
                    client=http_client,
                )
            error = not isinstance(img_bytes, bytes)
            if error:
                # Apply error status to client before we release it
                client.in_error = True
                client.error_time = time.time()

        if error:
            error_mes = img_bytes
            response = json_payload
            err_resp = make_error(error_mes, response, retry_count)
            if err_resp:
                return err_resp
            retry_count += 1
        else:
            break

    is_save_raw = server_config.get("save_directly", False)
    if not is_save_raw:
        img_pil = image_from_bytes(img_bytes)
        quality = server_config.get("compression_quality", 75)
        method = server_config.get("compression_method", 4)
        assert 0 <= quality <= 100, "Compression quality must be in [0, 100]"
        assert 0 <= method <= 6, "Compression method must be in [0, 6]"
        img_webp_bytes = process_image_as_webp(img_pil, quality, method)

    await asyncio.get_running_loop().run_in_executor(
        save_worker,
        save_img,
        save_path,
        safe_folder_name,
        img_bytes if is_save_raw else img_webp_bytes,
        json_payload,
    )

    return Response(img_bytes, media_type="image/png")


async def main(config: str):
    global server_config, auth_configs, generate_semaphore, nai_clients, retry_list
    server_config = toml.load(config)["gen_server"]
    auth_configs = server_config.get("auth", [])
    tokens = server_config.get("tokens", [])
    token = server_config.get("token", None)
    retry_list = set(server_config.get("retry_status_code", []))
    if token:
        tokens.append(token)
    if tokens:
        for token in tokens:
            client = await NAILocalClient.create(token)
            if client is None:
                print(f"Failed to create client for {token}")
            nai_clients[token] = client
    else:
        raise ValueError("No token provided, please set 'tokens' in config.toml")
    generate_semaphore = asyncio.Semaphore(
        server_config.get("max_jobs", 0) or len(nai_clients)
    )
    server = Server(
        Config(
            app=app,
            host=server_config["host"],
            port=server_config["port"],
        )
    )
    await server.serve()


@click.command()
@click.option(
    "-c",
    "--config",
    default="config.toml",
    help="Config file path",
    type=click.Path(exists=True),
)
def runner(config: str):
    asyncio.run(main(config))


if __name__ == "__main__":
    runner()
