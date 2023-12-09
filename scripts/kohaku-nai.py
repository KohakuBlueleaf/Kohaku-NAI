import asyncio
import sys
import random

import gradio as gr
import numpy as np
from PIL import Image

import torch
from torchvision.transforms.functional import to_tensor

from modules import shared, scripts, script_callbacks, images, devices
from modules.sd_samplers_common import images_tensor_to_samples
from modules.processing import Processed, StableDiffusionProcessingTxt2Img

from kohaku_nai.utils import (
    remote_gen,
    generate_novelai_image,
    set_client,
    image_from_bytes,
)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
loop = asyncio.new_event_loop()


async def run_tasks(tasks):
    return await asyncio.gather(*tasks)


class KohakuNAIScript(scripts.Script):
    def __init__(self):
        pass

    def title(self):
        return "Kohaku NAI Client"

    def show(self, is_img2img):
        return not is_img2img

    def ui(self, is_img2img):
        info = gr.Markdown("""### Please select the `Sampler` options here""")
        with gr.Row():
            sampler = gr.Dropdown(
                choices=[
                    "k_euler",
                    "k_euler_ancestral",
                    "k_dpmpp_2s_ancestral",
                    "k_dpmpp_2m",
                    "k_dpmpp_sde",
                    "ddim_v3",
                ],
                value="k_euler",
                label="Sampler",
                interactive=True,
            )
            scheduler = gr.Dropdown(
                choices=["native", "karras", "exponential", "polyexponential"],
                value="native",
                label="Scheduler",
                interactive=True,
            )
        with gr.Row():
            smea = gr.Checkbox(False, label="SMEA")
            dyn = gr.Checkbox(False, label="SMEA DYN")
        with gr.Row():
            dyn_threshold = gr.Checkbox(False, label="Dynamic Thresholding")
            cfg_rescale = gr.Slider(0, 1, 0, step=0.01, label="CFG rescale")

        return [info, sampler, scheduler, smea, dyn, dyn_threshold, cfg_rescale]

    def process(self, p, **kwargs):
        print(kwargs)
        return p

    def run(
        self,
        p: StableDiffusionProcessingTxt2Img,
        _,
        sampler,
        scheduler,
        smea,
        dyn,
        dyn_threshold,
        cfg_rescale,
    ):
        if p.scripts is not None:
            p.scripts.before_process(p)
        if p.seed == -1:
            p.seed = random.randint(0, 2**32 - 1)

        p.seeds = p.all_seeds = [p.seed + i for i in range(p.batch_size * p.n_iter)]
        p.setup_prompts()

        if p.scripts is not None:
            p.scripts.process(p)

        p.prompts = p.all_prompts
        p.negative_prompts = p.all_negative_prompts
        p.hr_prompts = p.all_hr_prompts
        p.hr_negative_prompts = p.all_hr_negative_prompts

        p.parse_extra_network_prompts()
        p.setup_conds()
        p.init(None, None, None)

        if shared.opts.knai_api_call == "Remote":
            login_status = loop.run_until_complete(
                (
                    set_client(
                        "httpx",
                        shared.opts.knai_remote_server.strip(),
                        shared.opts.knai_remote_server_pswd.strip(),
                    )
                )
            )
            datas = loop.run_until_complete(
                run_tasks(
                    [
                        remote_gen(
                            shared.opts.knai_remote_server,
                            p.prompts[i],
                            False,
                            p.negative_prompts[i],
                            "",
                            p.seeds[i],
                            p.cfg_scale,
                            p.width,
                            p.height,
                            p.steps,
                            sampler,
                            scheduler,
                            smea,
                            dyn,
                            dyn_threshold,
                            cfg_rescale,
                            shared.opts.knai_remote_server_ex_infos,
                        )
                        for i in range(p.batch_size)
                    ]
                )
            )
            imgs = [img for img, _ in datas]
            img_datas = [img_data for _, img_data in datas]
        else:
            set_client(shared.opts.knai_http_backend, token=shared.opts.knai_token.strip())
            datas = loop.run_until_complete(
                run_tasks(
                    [
                        generate_novelai_image(
                            p.prompts[i],
                            False,
                            p.negative_prompts[i],
                            "",
                            p.seeds[i],
                            p.cfg_scale,
                            p.width,
                            p.height,
                            p.steps,
                            sampler,
                            scheduler,
                            smea,
                            dyn,
                            dyn_threshold,
                            cfg_rescale,
                        )
                        for i in range(p.batch_size)
                    ]
                )
            )
            img_datas = [img_data for img_data, _ in datas]
            imgs = [
                image_from_bytes(img_data) if isinstance(img_data, bytes) else None
                for img_data in img_datas
            ]
        if any(img is None for img in imgs):
            failed_img_data = next(
                img_data for img_data in img_datas if not isinstance(img_data, bytes)
            )
            raise Exception("Failed to generate image: " + str(failed_img_data))
        nai_infos = [images.read_info_from_image(img) for img in imgs]

        if p.enable_hr:
            imgs_tensor = torch.stack([to_tensor(img.convert("RGB")) for img in imgs])
            imgs_latent = images_tensor_to_samples(imgs_tensor)

            with torch.no_grad(), p.sd_model.ema_scope(), (
                devices.without_autocast()
                if devices.unet_needs_upcast
                else devices.autocast()
            ):
                img_tensor_list = p.sample_hr_pass(
                    imgs_latent, imgs_tensor * 2 - 1, p.seeds, None, None, p.prompts
                )
                x_samples_ddim = torch.stack(img_tensor_list).float()
                x_samples_ddim = torch.clamp(
                    (x_samples_ddim + 1.0) / 2.0, min=0.0, max=1.0
                )
                imgs = []
                for i, x_sample in enumerate(x_samples_ddim):
                    x_sample = 255.0 * np.moveaxis(x_sample.cpu().numpy(), 0, 2)
                    x_sample = x_sample.astype(np.uint8)
                    imgs.append(Image.fromarray(x_sample))

        extra_infos = {
            "Script": self.title(),
            "Sampler": sampler != "k_euler" and sampler,
            "Scheduler": scheduler != "native" and scheduler,
            "SMEA": smea,
            "Dynamic": dyn,
            "Dynamic Thresholding": dyn_threshold,
            "CFG rescale": cfg_rescale,
            **p.extra_generation_params,
        }
        extra_info_text = ", ".join([f"{k}: {v}" for k, v in extra_infos.items() if v])
        infotexts = [f"{exif}, {extra_info_text}" for exif, _ in nai_infos]

        for img, (exif, items) in zip(imgs, nai_infos):
            images.save_image(
                img,
                p.outpath_samples,
                "",
                p.seed,
                p.prompt,
                shared.opts.samples_format,
                info=f"{exif}, {extra_info_text}",
                p=p,
            )

        if len(imgs) > 1:
            img_grid = images.image_grid(imgs, p.batch_size)
            imgs = [img_grid] + imgs
            infotexts = infotexts[:1] + infotexts
            seeds = [p.seed] + p.seeds
        else:
            seeds = p.seeds

        res = Processed(p, imgs, seed=seeds, infotexts=infotexts)
        return res


def on_ui_settings():
    section = ("kohaku-nai", "Kohaku-NAI")
    shared.opts.add_option(
        "knai_api_call",
        shared.OptionInfo(
            "Remote",
            "API call from",
            gr.Radio,
            {"choices": ["Remote", "Local"]},
            section=section,
        ).info("Call NAI api directly from client or use generation server"),
    )
    shared.opts.add_option(
        "knai_http_backend",
        shared.OptionInfo(
            "httpx",
            "HTTP backend",
            gr.Radio,
            {"choices": ["httpx", "curl_cffi"]},
            section=section,
        ).info("Call NAI api via httpx or curl_cffi"),
    )
    shared.opts.add_option(
        "knai_token", shared.OptionInfo("", "Token for local call", section=section)
    )
    shared.opts.add_option(
        "knai_remote_server",
        shared.OptionInfo(
            "http://127.0.0.1:7000", "Remote server URL", section=section
        ),
    )
    shared.opts.add_option(
        "knai_remote_server_pswd",
        shared.OptionInfo("", "Remote server PASSWORD", section=section),
    )
    shared.opts.add_option(
        "knai_remote_server_ex_infos",
        shared.OptionInfo(
            "{}",
            "Extra info for remote",
            gr.Code,
            {"language": "json"},
            section=section,
        ).info(
            "The extra infos in JSON which will be sent to remote server when generating"
        ),
    )


script_callbacks.on_ui_settings(on_ui_settings)
