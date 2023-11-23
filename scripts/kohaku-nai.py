import asyncio
import sys
import gradio as gr

from modules import shared
from modules import scripts
from modules import script_callbacks
from modules import images
from modules.processing import Processed

from utils import remote_gen, generate_novelai_image, set_token, remote_login, image_from_bytes

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
loop = asyncio.new_event_loop()


class KohakuNAIScript(scripts.Script):
    def __init__(self):
        pass

    def title(self):
        return "Kohaku NAI Client"

    def show(self, is_img2img):
        return not is_img2img

    def ui(self, is_img2img):
        info = gr.Markdown('''
        ### Please select the `Sampler` options here
        ''')
        with gr.Row():
            sampler = gr.Dropdown(
                choices=[
                    "k_euler", "k_euler_ancestral", "k_dpmpp_2s_ancestral", 
                    "k_dpmpp_2m", "k_dpmpp_sde", "ddim_v3"
                ],
                value="k_euler",
                label="Sampler",
                interactive=True
            )
            scheduler = gr.Dropdown(
                choices=[
                    "native", "karras", "exponential", "polyexponential"
                ],
                value="native",
                label="Scheduler",
                interactive=True
            )
        with gr.Row():
            smea = gr.Checkbox(False, label="SMEA")
            dyn = gr.Checkbox(False, label="SMEA DYN")
        with gr.Row():
            dyn_threshold = gr.Checkbox(False, label="Dynamic Thresholding")
            cfg_rescale = gr.Slider(0, 1, 0, step=0.01, label="CFG rescale")

        return [
            info,
            sampler,
            scheduler,
            smea,
            dyn,
            dyn_threshold,
            cfg_rescale
        ]
    
    def process(self, p, **kwargs):
        print(kwargs)
        return p

    def run(self, p, _, sampler, scheduler, smea, dyn, dyn_threshold, cfg_rescale):
        if shared.opts.knai_api_call == 'Remote':
            login_status = loop.run_until_complete((
                remote_login(
                    shared.opts.knai_remote_server.strip(), 
                    shared.opts.knai_remote_server_pswd.strip()
                )
            ))
            img, img_data = loop.run_until_complete((
                remote_gen(
                    shared.opts.knai_remote_server,
                    p.prompt,
                    "",
                    p.negative_prompt,
                    p.seed,
                    p.cfg_scale,
                    p.width,
                    p.height,
                    p.steps,
                    sampler,
                    scheduler,
                    smea,
                    dyn,
                    dyn_threshold,
                    cfg_rescale
                )
            ))
        else:
            set_token(shared.opts.knai_token)
            img_data, _ = loop.run_until_complete((
                generate_novelai_image(
                    p.prompt,
                    p.negative_prompt,
                    p.seed,
                    p.cfg_scale,
                    p.width,
                    p.height,
                    p.steps,
                    sampler,
                    scheduler,
                    smea,
                    dyn,
                    dyn_threshold,
                    cfg_rescale
                )
            ))
            if not isinstance(img_data, bytes):
                img = None
            else:
                img = image_from_bytes(img_data)
        if img is None:
            raise Exception("Failed to generate image: " + str(img_data))
        exif, items = images.read_info_from_image(img)
        extra_infos = {
            'Script': self.title(),
            'Sampler': sampler != 'k_euler' and sampler,
            'Scheduler': scheduler != 'native' and scheduler,
            'SMEA': smea,
            'Dynamic': dyn,
            'Dynamic Thresholding': dyn_threshold,
            'CFG rescale': cfg_rescale
        }
        extra_info_text = ", ".join([f"{k}: {v}" for k, v in extra_infos.items() if v])
        res = Processed(
            p, [img], seed=p.seed, info=f'{exif}, {extra_info_text}'
        )
        images.save_image(
            img, p.outpath_samples, "", p.seed, p.prompt, 
            shared.opts.samples_format,
            info = f'{exif}, {extra_info_text}', p = p
        )
        return res


def on_ui_settings():
    section = ('kohaku-nai', "Kohaku-NAI")
    shared.opts.add_option(
        "knai_api_call",
        shared.OptionInfo(
            "Remote", "API call from", gr.Radio, {"choices": ["Remote", "Local"]}, section=section
        ).info("Call NAI api directly from client or use generation server")
    )
    shared.opts.add_option(
        "knai_token",
        shared.OptionInfo(
            "", "Token for local call", section=section
        )
    )
    shared.opts.add_option(
        "knai_remote_server",
        shared.OptionInfo(
            "http://127.0.0.1:7000", "Remote server URL", section=section
        )
    )
    shared.opts.add_option(
        "knai_remote_server_pswd",
        shared.OptionInfo(
            "", "Remote server PASSWORD", section=section
        )
    )


script_callbacks.on_ui_settings(on_ui_settings)