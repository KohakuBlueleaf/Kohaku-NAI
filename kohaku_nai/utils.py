
import re
import io
import json
import piexif
from typing import Any

from PIL import Image

import api
from api.image import (
    QUALITY_TAGS,
    UCPRESET,
)


file_name_cleaner = re.compile(r"[^a-zA-Z0-9_.-]")


def make_file_name(args: dict[str, Any]):
    prompt = args.pop("prompt", "")[:20]
    neg_prompt = args.pop("negative_prompt", "")[:20]
    file_name = f"{prompt}_{neg_prompt}_" + "_".join(
        [f"{k}={v}" for k, v in args.items()]
    )
    return file_name_cleaner.sub("", file_name)


async def remote_gen(
    end_point="http://127.0.0.1:7000",
    prompt="",
    quality_tags=False,
    negative_prompt="",
    ucpreset="",
    seed=-1,
    scale=5.0,
    width=1024,
    height=1024,
    steps=28,
    sampler="k_euler",
    schedule="native",
    smea=False,
    dyn=False,
    dyn_threshold=False,
    cfg_rescale=0,
    extra_infos={},
    model="nai-diffusion-3",
    priority=0,
    **kwargs,
):
    if kwargs:
        print(f"Unused kwargs: {kwargs.keys()}")
    payload = {
        "prompt": f"{prompt}, {QUALITY_TAGS}" if quality_tags else prompt,
        "neg_prompt": (
            f"{UCPRESET[ucpreset]}, {negative_prompt}"
            if ucpreset in UCPRESET
            else negative_prompt
        ),
        "seed": seed,
        "scale": scale,
        "width": width,
        "height": height,
        "steps": steps,
        "sampler": sampler,
        "schedule": schedule,
        "smea": smea,
        "dyn": dyn,
        "dyn_threshold": dyn_threshold,
        "cfg_rescale": cfg_rescale,
        "extra_infos": (
            extra_infos
            if isinstance(extra_infos, str)
            else json.dumps(extra_infos, ensure_ascii=False)
        ),
        "model": model,
        "priority": priority,
    }
    response = await api.global_client.post(f"{end_point}/gen", json=payload)
    if response.status_code == 200:
        mem_file = io.BytesIO(response.content)
        mem_file.seek(0)
        return Image.open(mem_file), response.content
    else:
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = response.content
        return None, data


def free_check(width: int, height: int, steps: int):
    return width * height <= 1024 * 1024 and steps <= 28


def image_from_bytes(data: bytes):
    img_file = io.BytesIO(data)
    img_file.seek(0)
    return Image.open(img_file)


def process_image_as_webp(
    image: Image,
    quality: int = 75,
    method: int = 4,
    metadata: dict[str, Any] = None,
) -> bytes:
    """
    encode image as webp.

    See:
        https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp

    Args:
        image (Image): a PIL image, assumed to be generated by NovelAI and with metadata in pnginfo
        quality (int, optional): webp compression quality. Defaults to 75.
        method (int, optional): webp compression method. Defaults to 4.
        metadata (dict[str, Any], optional): `metadata` be directly encoded as Exif, if provided. Defaults to None.

    Returns:
        bytes: the encoded image
    """
    metadata_bytes: bytes | None = None
    if metadata:
        metadata_bytes = piexif.dump(metadata)
    else:
        # Try to read metadata from image.  Note that `image.info` will return a
        # dict that NOT include `exif` field if the image is generated by
        # NovelAI.  NovelAI embeds metadata in pnginfo, which is different from
        # exif.  (exif just a field in pnginfo in this case)
        items = (image.info or {}).copy()
        if len(items) > 0:
            # WebP only support save exif in the metadata. So we put everything
            # in UserComment field
            #
            # The bad news is that the code from AUTOMATIC1111 still can't read
            # from it directly. To address this a custom schema mapping is
            # required (which leads to replace the whole Exif.UserComment field
            # and loss the original metadata) or modification on
            # `read_info_from_image` function in AUTOMATIC1111
            if "Comment" in items:
                try:
                    comment_str = items["Comment"]
                    # Let's unmarsal then marshal it for aesthetic
                    json_info = json.loads(comment_str)
                    items["Comment"] = json_info
                except json.JSONDecodeError:
                    pass
            # https://exiftool.org/TagNames/EXIF.html
            # 0x9286 UserComment
            metadata_bytes = piexif.dump(
                {"Exif": {0x9286: bytes(json.dumps(items, indent=4), "utf-8")}}
            )

    ret = io.BytesIO()
    if metadata_bytes:
        image.save(
            ret,
            format="webp",
            quality=quality,
            method=method,
            lossless=False,
            exact=False,
            exif=metadata_bytes,
        )
    else:
        image.save(
            ret,
            format="webp",
            quality=quality,
            method=method,
            lossless=False,
            exact=False,
        )
    ret.seek(0)
    return ret.read()


class GenerationError(Exception):
    pass