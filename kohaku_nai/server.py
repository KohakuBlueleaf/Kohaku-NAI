import asyncio
import os
import re
import json
import time
import random
import click
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
    process_image,
    HttpClient
)
from kohaku_nai.request import GenerateRequest
from kohaku_nai.config_spec import GenServerConfig

id_gen = SnowflakeGenerator(1)

server_config: None | GenServerConfig = None
auth_configs: list[GenServerConfig] = []
nai_clients: dict[str, 'NAILocalClient'] = {}
prev_gen_time = time.time()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=uuid4().hex)

generate_semaphore: None | asyncio.Semaphore = None
save_worker = ThreadPoolExecutor(16)


class NAILocalClient:
    def __init__(self, token, client: HttpClient):
        self.token = token
        self.client = client
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
            return {"status": "login success"}
    else:
        request.session.clear()
        return Response(json.dumps({"status": "login failed"}), 403)


@app.post("/gen")
async def gen(context: GenerateRequest, request: Request):
    global prev_gen_time

    is_signed = request.session.get("signed", False)
    is_free_only = request.session.get("free_only", True)
    try:
        extra_infos = json.loads(context.extra_infos)
    except:
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
        # Wait for available client, if none available, switch the control back to eventloop
        while True:
            for client in nai_clients.values():
                if client.available:
                    break
            else:
                await asyncio.sleep(0)
                continue
            break

        async with client as http_client:
            async with generate_semaphore:
                if prev_gen_time + server_config["min_delay"] > time.time():
                    await asyncio.sleep(server_config["min_delay"] + random.random() * 0.3)
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

        if not isinstance(img_bytes, bytes):
            error_mes = img_bytes
            response = json_payload
            try:
                error_response = response.json()
                if 'statusCode' in error_response:
                    status_code = error_response['statusCode']
                    current_time = time.time()
                    retry_list = server_config.get("retry_status_code", [])
                    if status_code in server_config.get("retry_status_code", []):
                        retry_count += 1
                        if retry_count > server_config["max_retry_times"]:
                            return Response(
                                json.dumps({"error-mes": error_mes, "status": error_response}), 408
                            )
                        if server_config["retry_delay"] > 0:
                            await asyncio.sleep(server_config["retry_delay"])
                        continue
            except:
                error_response = response.text
            return Response(
                json.dumps({"error-mes": error_mes, "status": error_response}), 500
            )
        else:
            break

    is_save_raw = server_config.get("save_directly", False)
    if not is_save_raw:
        img = image_from_bytes(img_bytes)
        quality = server_config.get("compression_quality", 75)
        method = server_config.get("compression_method", 4)
        assert 0 <= quality <= 100, "Compression quality must be in [0, 100]"
        assert 0 <= method <= 6, "Compression method must be in [0, 6]"
        # https://exiftool.org/TagNames/EXIF.html
        # 0x9286 UserComment
        metadata = {"Exif": {0x9286: bytes(json_payload, "utf-8")}}
        img_bytes = process_image(img, metadata, quality, method)

    await asyncio.get_running_loop().run_in_executor(
        save_worker, save_img, save_path, safe_folder_name, img_bytes, json_payload
    )
    media_type = "image/png" if is_save_raw else "image/webp"

    return Response(img_bytes, media_type=media_type)


async def main(config: str):
    global server_config, auth_configs, generate_semaphore, nai_clients
    server_config = toml.load(config)["gen_server"]
    auth_configs = server_config.get("auth", [])
    tokens = server_config.get("tokens", [])
    token = server_config.get("token", None)
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
    generate_semaphore = asyncio.Semaphore(server_config.get("max_jobs", 0) or len(nai_clients))
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
