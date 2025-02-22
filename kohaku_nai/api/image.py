import random
import io
import zipfile
import json
from httpx import AsyncClient
from curl_cffi.requests import AsyncSession
from .. import api


API_IMAGE_URL = "https://image.novelai.net"
HttpClient = AsyncClient | AsyncSession


QUALITY_TAGS = "best quality, amazing quality, very aesthetic, absurdres"
UCPRESET = {
    "Heavy": (
        "lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, "
        "bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, "
        "artistic error, username, scan, [abstract]"
    ),
    "Light": "lowres, jpeg artifacts, worst quality, watermark, blurry, very displeasing",
    "None": "lowres",
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
    "schedule": "native",
    "smea": False,
    "dyn": False,
    "dyn_threshold": False,
    "cfg_rescale": 0,
    "images": 1,
    "model": "nai-diffusion-3",
}
MODEL_LIST = [
    "nai-diffusion",
    "safe-diffusion",
    "nai-diffusion-furry",
    "custom",
    "nai-diffusion-inpainting",
    "nai-diffusion-3-inpainting",
    "safe-diffusion-inpainting",
    "furry-diffusion-inpainting",
    "kandinsky-vanilla",
    "nai-diffusion-2",
    "nai-diffusion-3",
    "nai-diffusion-4-curated-preview"
]


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
    schedule="native",
    smea=False,
    dyn=False,
    dyn_threshold=False,
    cfg_rescale=0,
    model="nai-diffusion-3",
    client: HttpClient | None = None,
    **kwargs,
):
    if kwargs:
        print(f"Unused kwargs: {kwargs.keys()}")
    if client is None:
        client = api.global_client
    # Assign a random seed if seed is -1
    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    # Define the payload
    payload = {
        "action": "generate",
        "input": f"{prompt}, {QUALITY_TAGS}" if quality_tags else prompt,
        "model": "nai-diffusion-3" if model not in MODEL_LIST else model,
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
            "negative_prompt": (
                f"{UCPRESET[ucpreset]}, {negative_prompt}"
                if ucpreset in UCPRESET
                else negative_prompt
            ),
            "noise_schedule": schedule,
            "qualityToggle": True,
            "seed": seed,
            "sm": smea,
            "sm_dyn": dyn,
            "uncond_scale": 1,
        },
    }

    # Send the POST request
    response = await client.post(f"{API_IMAGE_URL}/ai/generate-image", json=payload)

    # Process the response
    if response.headers.get("Content-Type") == "binary/octet-stream":
        zipfile_in_memory = io.BytesIO(response.content)
        with zipfile.ZipFile(zipfile_in_memory, "r") as zip_ref:
            file_names = zip_ref.namelist()
            if file_names:
                with zip_ref.open(file_names[0]) as file:
                    return file.read(), json.dumps(
                        payload, ensure_ascii=False, indent=2
                    )
            else:
                return "NAI doesn't return any images", response
    else:
        return "Generation failed", response