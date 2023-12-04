import asyncio
from enum import Enum

import click
import httpx
from loguru import logger

from .request import GenerateRequest


class AspectRatio(str, Enum):
    Horizontal = "h"
    Vertical = "v"
    UltraWide = "u"
    UltraTall = "t"
    Square = "s"


ar_map: dict[AspectRatio, tuple[int, int]] = {
    AspectRatio.Horizontal: (1216, 832),
    AspectRatio.Vertical: (832, 1216),
    AspectRatio.UltraWide: (1472, 704),
    AspectRatio.UltraTall: (704, 1472),
}


@click.command()
@click.option("--prompt", "-p", default="1girl", help="Prompt to generate from")
@click.option(
    "--negative", "-n", default="bad quality", help="Negative prompt to generate from"
)
@click.option("--seed", "-s", default=-1, help="Seed to generate from")
@click.option("--scale", "-S", default=5.0, help="Scale to generate from")
@click.option("--width", "-w", help="Width to generate from")
@click.option("--height", "-h", help="Height to generate from")
@click.option("--steps", "-t", default=28, help="Steps")
@click.option(
    "--sampler",
    "-m",
    default="k_euler",
    help="Sampler",
    type=click.Choice(
        [
            "k_euler",
            "k_euler_ancestral",
            "k_dpmpp_2s_ancestral",
            "k_dpmpp_2m",
            "k_dpmpp_sde",
            "ddim_v3",
        ]
    ),
)
@click.option("--schedule", default="native", help="Schedule")
@click.option("--smea", is_flag=True, help="SMEA for sampler")
@click.option("--dyn", is_flag=True, help="Dyn for sampler")
@click.option("--dyn-threshold", is_flag=True, help="Dyn threshold for sampler")
@click.option("--cfg-rescale", default=0, help="CFG rescale")
@click.option("--sub-folder", default="", help="Sub folder to save to")
@click.option("--ar", type=click.Choice(AspectRatio))
@click.option(
    "--host", default="127.0.0.1:7000", help="the host (gen server) to connect to"
)
@click.option("--auth", help="the auth password to use")
def main(
    prompt: str,
    negative: str,
    seed: int,
    scale: float,
    width: int | None,
    height: int | None,
    steps: int,
    sampler: str,
    schedule: str,
    smea: bool,
    dyn: bool,
    dyn_threshold: bool,
    cfg_rescale: bool,
    ar: AspectRatio | None,
    host: str,
    sub_folder: str,
    auth: str | None,
):
    if auth is not None:
        raise NotImplementedError("Auth is not implemented yet")
    w = width
    h = height
    if ar is not None:
        if w is not None and h is not None:
            logger.warning("Both width and height are specified, ignoring aspect ratio")
        else:
            w, h = ar_map[ar]
            logger.info(f"Using aspect ratio {ar.name} ({w}x{h})")
    if w is None or h is None:
        logger.warning("Width or height is not specified, using default 1024x1024")
        w = 1024
        h = 1024
    smea_t = " smea" if smea else ""
    dyn_t = " dyn" if dyn else ""
    rescale = f" rescale={cfg_rescale}" if cfg_rescale else ""
    logger.info(
        f"{w}x{h}@{steps} with {sampler} ({schedule}{smea_t}{dyn_t}) at cfg {scale}{rescale}"
    )
    req = GenerateRequest(
        prompt=prompt,
        neg_prompt=negative,
        seed=seed,
        scale=scale,
        width=w,
        height=h,
        steps=steps,
        sampler=sampler,
        schedule=schedule,
        smea=smea,
        dyn=dyn,
        dyn_threshold=dyn_threshold,
        cfg_rescale=cfg_rescale,
    )
    asyncio.run(send_req(host, req, sub_folder))


async def send_req(host: str, req: GenerateRequest, sub_folder: str = ""):
    async with httpx.AsyncClient(timeout=60) as client:
        host = f"http://{host}/gen" if not host.startswith("http") else host
        dump = req.model_dump()
        dump["extra_infos"] = "{}"
        dump["sub_folder"] = sub_folder
        resp = await client.post(host, json=dump)
        media_type = resp.headers["Content-Type"]
        is_img = media_type.startswith("image")
        if not is_img:
            logger.info("Response: {}", resp.text)
        else:
            logger.info("success")
        resp.raise_for_status()


if __name__ == "__main__":
    main()
