import random
import io
import zipfile
import json

from PIL import Image
from httpx import AsyncClient
from curl_cffi.requests import AsyncSession


jwt_token = ''
url = "https://api.novelai.net/ai/generate-image"
global_client = AsyncSession(timeout=3600, impersonate='chrome110')


def set_token(token):
    global jwt_token, global_client
    if jwt_token == token:
        return
    jwt_token = token
    global_client = AsyncSession(
        timeout=3600,
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
            "Origin": "https://novelai.net",
            "Referer": "https://novelai.net/"
        }, 
        impersonate='chrome110',
    )


async def remote_login(end_point, password):
    payload = {"password": password}
    response = await global_client.post(f'{end_point}/login', params=payload)
    if response.status_code == 200:
        return response.json()["status"]
    else:
        return None


QUALITY_TAGS = "best quality, amazing quality, very aesthetic, absurdres"
UCPRESET = {
    "heavy": (
        "lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, "
        "bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, "
        "artistic error, username, scan, [abstract]"
    ),
    "light": "lowres, jpeg artifacts, worst quality, watermark, blurry, very displeasing",
    "None": "lowres"
}
DEFAULT_ARGS = {
    "prompt": "",
    "negative_prompt": "",
    "quality_tags": False,
    "ucpreset": "",
    "seed": -1, 
    "scale": 5.0, 
    "width": 1024, 
    "height": 1024, 
    "steps": 28, 
    "sampler": "k_euler",
    "schedule": 'native',
    "smea": False,
    "dyn": False,
    "dyn_threshold": False,
    "cfg_rescale": 0,
}


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
    schedule='native',
    smea=False,
    dyn=False,
    dyn_threshold=False,
    cfg_rescale=0,
    extra_infos = '',
):
    payload = {
        "prompt": f'{prompt}, {QUALITY_TAGS}' if quality_tags else prompt,
        "neg_prompt": f'{UCPRESET[ucpreset]}, {negative_prompt}' if ucpreset in UCPRESET else negative_prompt,
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
    }
    response = await global_client.post(f'{end_point}/gen', json=payload)
    if response.status_code == 200:
        mem_file = io.BytesIO(response.content)
        mem_file.seek(0)
        return Image.open(mem_file), response.content
    else:
        try:
            data = response.json()
        except:
            data = response.content
        return None, data


async def generate_novelai_image(
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
    schedule='native',
    smea=False,
    dyn=False,
    dyn_threshold=False,
    cfg_rescale=0,
):
    # Assign a random seed if seed is -1
    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    # Define the payload
    payload = {
        "action": "generate",
        "input": f'{prompt}, {QUALITY_TAGS}' if quality_tags else prompt,
        "model": "nai-diffusion-3",
        "parameters": {
            "width": width,
            "height": height,
            "scale": scale,
            "sampler": sampler,
            "steps": steps,
            "n_samples": 1,
            "ucPreset": 0,
            "add_original_image": False,
            "cfg_rescale": cfg_rescale,
            "controlnet_strength": 1,
            "dynamic_thresholding": dyn_threshold,
            "legacy": False,
            "negative_prompt": f'{UCPRESET[ucpreset]}, {negative_prompt}' if ucpreset in UCPRESET else negative_prompt,
            "noise_schedule": schedule,
            "qualityToggle": True,
            "seed": seed,
            "sm": smea,
            "sm_dyn": dyn,
            "uncond_scale": 1,
        }
    }

    # Send the POST request
    response = await global_client.post(url, json=payload)

    # Process the response
    if response.headers.get('Content-Type') == 'application/x-zip-compressed':
        zipfile_in_memory = io.BytesIO(response.content)
        with zipfile.ZipFile(zipfile_in_memory, 'r') as zip_ref:
            file_names = zip_ref.namelist()
            if file_names:
                with zip_ref.open(file_names[0]) as file:
                    return file.read(), json.dumps(payload, ensure_ascii=False, indent=2)
            else:
                return "NAI doesn't return any images", response
    else:
        return "Generation failed", response


def free_check(width, height, steps):
    return width * height <= 1024 * 1024 and steps<=28


def image_from_bytes(data):
    img_file = io.BytesIO(data)
    img_file.seek(0)
    return Image.open(img_file)