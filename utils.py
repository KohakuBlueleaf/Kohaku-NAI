import random
import io
import zipfile
import json

from PIL import Image
from httpx import AsyncClient


jwt_token = ''
url = "https://api.novelai.net/ai/generate-image"
global_client = AsyncClient(timeout=100)


def set_token(token):
    global jwt_token, global_client
    if jwt_token == token:
        return
    jwt_token = token
    global_client = AsyncClient(
        timeout=100,
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
            "Origin": "https://novelai.net",
            "Referer": "https://novelai.net/"
        }
    )


async def remote_login(end_point, password):
    payload = {"password": password}
    response = await global_client.post(f'{end_point}/login', params=payload)
    if response.status_code == 200:
        return response.json()["status"]
    else:
        return None


async def remote_gen(
    end_point="http://127.0.0.1:7000",
    input_text="",
    quality_tags="",
    negative_prompt="", 
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
    chg_rescale=0,
):
    payload = {
        "prompt": f'{input_text}, {quality_tags}',
        "neg_prompt": negative_prompt,
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
        "chg_rescale": chg_rescale,
    }
    response = await global_client.post(f'{end_point}/gen', json=payload)
    if response.status_code == 200:
        mem_file = io.BytesIO(response.content)
        mem_file.seek(0)
        return Image.open(mem_file)
    else:
        return None


async def generate_novelai_image(
    input_text="", 
    negative_prompt="", 
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
        "input": input_text,
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
            "negative_prompt": negative_prompt,
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