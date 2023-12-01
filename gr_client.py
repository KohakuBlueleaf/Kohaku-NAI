import os
from hashlib import sha3_256

import toml
import json
import gradio as gr

from utils import remote_gen, remote_login, set_token, generate_novelai_image, image_from_bytes
from client_modules import extension


client_config: dict = toml.load("config.toml")['client']
extra_infos = client_config.get('remote_extra_infos', {})


def control_ui():
    prompt = gr.TextArea(
        label="Prompt", lines=3,
        value = client_config['default_prompt'],
    )
    neg_prompt = gr.TextArea(
        label="Negative Prompt", lines=1,
        value=client_config['default_neg'],
    )
    with gr.Row():
        with gr.Column(scale=3, min_width=160):
            enable_quality_tags = gr.Checkbox(label="Enable Quality Tags", value=True)
        with gr.Column(scale=5, min_width=360):
            neg_preset = gr.Radio(
                choices=["Heavy", "Light", "None", "Empty"],
                value="Light",
                label="UC Preset",
            )
    with gr.Row():
        seed = gr.Number(label="Seed", value=-1, step=1, maximum=2**32-1, minimum=-1)
        sampler = gr.Dropdown(
            choices=[
                "k_euler", "k_euler_ancestral", "k_dpmpp_2s_ancestral", 
                "k_dpmpp_2m", "k_dpmpp_sde", "ddim_v3"
            ],
            value="k_euler",
            label="Sampler",
            interactive=True
        )
        scale = gr.Slider(label="Scale", value=5.0, minimum=1, maximum=10, step=0.1)
        steps = gr.Slider(label="Steps", value=28, minimum=1, maximum=50, step=1)
    with gr.Row():
        width = gr.Slider(label="Width", value=1024, minimum=64, maximum=2048, step=64)
        height = gr.Slider(label="Height", value=1024, minimum=64, maximum=2048, step=64)
    
    gen_btn = gr.Button(value="Generate", variant="primary")
    return gen_btn, [width, height], [prompt, enable_quality_tags, neg_prompt, neg_preset, seed, scale, width, height, steps, sampler]


def settings_ui():
    with gr.Row():
        with gr.Column():
            gr.Markdown('### Advance Generation settings')
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
        
        with gr.Column():
            gr.Markdown('### Client settings')
            mode = gr.Radio(['remote', 'local'], value=client_config['mode'], label="Mode")
            with gr.Column(visible=client_config['mode']=='remote') as remote_blk:
                end_point = gr.Textbox(client_config['end_point'], label="End Point")
                end_point_pswd = gr.Textbox(client_config['end_point_pswd'], label="End Point Password", type="password")
                extra_info_json = gr.Code(
                    value=json.dumps(extra_infos, ensure_ascii=False, indent=2),
                    label="Remote Extra Infos",
                    language='json'
                )
            with gr.Column(visible=client_config['mode']=='local') as local_blk:
                token = gr.Textbox(client_config['token'], label="Token")
            
            mode.change(lambda m: gr.update(visible= m=='remote'), mode, remote_blk)
            mode.change(lambda m: gr.update(visible= m=='local'), mode, local_blk)
    return [scheduler, smea, dyn, dyn_threshold, cfg_rescale, extra_info_json], [mode, end_point, end_point_pswd, token]


async def generate(mode, end_point, end_point_pswd, token, prompt, enable_quality_tags, neg_prompt, neg_preset, seed, scale, width, height, steps, sampler, scheduler, smea, dyn, dyn_threshold, cfg_rescale, extra_info_json):
    prompt = extension.process_prompt(prompt)
    neg_prompt = extension.process_prompt(neg_prompt)
    
    if mode == 'remote':
        if (pswd:=end_point_pswd) or (pswd:=client_config['end_point_pswd']):
            await remote_login(end_point, pswd)
        img, img_data = await remote_gen(
            end_point,
            prompt, enable_quality_tags, neg_prompt, neg_preset, seed, scale, 
            width, height, steps, sampler, scheduler, 
            smea, dyn, dyn_threshold, cfg_rescale, extra_info_json
        )
    elif mode == 'local':
        set_token(token)
        img_data, _ = await generate_novelai_image(
            prompt, enable_quality_tags, neg_prompt, neg_preset, neg_prompt, seed, scale, 
            width, height, steps, sampler, scheduler, 
            smea, dyn, dyn_threshold, cfg_rescale
        )
        if not isinstance(img_data, bytes):
            return None
        img = image_from_bytes(img_data)
    else:
        return None
    
    if img is None:
        return None
    
    if client_config['autosave']:
        save_path = client_config['save_path']
        os.makedirs(name=save_path, exist_ok=True)
        img_hash = sha3_256(img_data).hexdigest()
        with open(os.path.join(save_path, f'{img_hash}.png'), 'wb') as f:
            f.write(img_data)
    
    return [img]


def preview_ui():
    with gr.Blocks(css='#preview_image { height: 100%;}') as page:
        h_slider = gr.Slider(label="Height", value=500, minimum=100, maximum=1200, step=10)
        image = gr.Gallery(elem_id='preview_image', height=500)
    h_slider.change(lambda h: gr.Gallery(height=h), h_slider, image)
    return image


def main_ui():
    with gr.Blocks() as page:
        with gr.Row(variant="panel"):
            with gr.Column():
                with gr.Tabs():
                    with gr.TabItem('Gen'):
                        gen_btn, (width, height), controls = control_ui()
                    with gr.TabItem('Settings'):
                        adv_controls, modes = settings_ui()
            with gr.Column():
                image = preview_ui()
    mode = modes[0]
    width.change(
        lambda w, h, mode: h if mode=='local' or w*h<=1024*1024 else (1024*1024//w//64)*64, 
        [width, height, mode], height, show_progress=False
    )
    height.change(
        lambda w, h, mode: w if mode=='local' or w*h<=1024*1024 else (1024*1024//h//64)*64, 
        [width, height, mode], width, show_progress=False
    )
    gen_btn.click(generate, modes+controls+adv_controls, image)
    return page


def util_ui():
    with gr.Blocks() as page:
        gr.Text('WIP')
    return page


def ui():
    with gr.Blocks(title="NAI Client by Kohaku") as website:
        with gr.Tabs():
            with gr.TabItem("Main"):
                main_ui()
            with gr.TabItem("Util"):
                util_ui()
    return website


if __name__ == '__main__':
    extension.load_extensions()
    website = ui()
    website.launch()
    input('Press Enter to close...')