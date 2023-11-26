import os
from hashlib import sha3_256

import toml
import gradio as gr

from utils import remote_gen, remote_login, set_token, generate_novelai_image, image_from_bytes
from client_modules import extension


client_config = toml.load("config.toml")['client']


def control_ui():
    prompt = gr.TextArea(label="Prompt", lines=3)
    quality_tags = gr.TextArea(
        label="Quality Tags", lines=1,
        value=client_config['default_quality'],
    )
    neg_prompt = gr.TextArea(
        label="Negative Prompt", lines=1,
        value=client_config['default_neg'],
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
    with gr.Row():
        with gr.Column():
            with gr.Accordion('Advanced Gen Setting', open=False):
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
            with gr.Accordion('Client Setting', open=False):
                mode = gr.Radio(['remote', 'local'], value=client_config['mode'], label="Mode")
                end_point = gr.Textbox(client_config['end_point'], label="End Point")
                token = gr.Textbox(client_config['token'], label="Token")
    
    gen_btn = gr.Button(value="Generate", variant="primary")
    width.change(lambda w, h: h if mode=='local' or w*h<=1024*1024 else (1024*1024//w//64)*64, [width, height], height)
    height.change(lambda w, h: w if mode=='local' or w*h<=1024*1024 else (1024*1024//h//64)*64, [width, height], width)
    return gen_btn, [mode, end_point, token], [prompt, quality_tags, neg_prompt, seed, scale, width, height, steps, sampler, scheduler, smea, dyn, dyn_threshold, cfg_rescale]


async def generate(mode, end_point, token, prompt, quality_tags, neg_prompt, seed, scale, width, height, steps, sampler, scheduler, smea, dyn, dyn_threshold, cfg_rescale):
    prompt = extension.process_prompt(prompt)
    neg_prompt = extension.process_prompt(neg_prompt)
    quality_tags = extension.process_prompt(quality_tags)
    
    print(prompt, quality_tags, neg_prompt)
    
    if mode == 'remote':
        if pswd:=client_config['end_point_pswd']:
            await remote_login(end_point, pswd)
        img, img_data = await remote_gen(
            end_point,
            prompt, quality_tags, neg_prompt, "", seed, scale, 
            width, height, steps, sampler, scheduler, 
            smea, dyn, dyn_threshold, cfg_rescale
        )
    elif mode == 'local':
        set_token(token)
        img_data, _ = await generate_novelai_image(
            prompt, quality_tags, neg_prompt, "", neg_prompt, seed, scale, 
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
                gen_btn, modes, controls = control_ui()
            with gr.Column():
                image = preview_ui()
    gen_btn.click(generate, modes+controls, image)
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