# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午1:56
# @Author  : sudoskys
# @File    : command.py
# @Software: PyCharm
from typing import Annotated

from arclet.alconna import Alconna, Args, Option, CommandMeta

DrawCommand = Alconna(
    "/draw",
    Args['prompt', str],
    Option("--negative_prompt", Args.negative_prompt[str], help_text="设置负面提示"),
    Option("--seed", Args['seed', int], help_text="设置随机种子"),
    Option("--steps", Args['steps', Annotated[int, lambda x: x < 70]], help_text="设置步数"),
    Option("--scale", Args['scale', int], help_text="设置cfg_rescale"),
    Option("--sampler", Args[
        "sampler", ["k_euler", "k_euler_ancestral", "k_dpmpp_2s_ancestral", "k_dpmpp_2m", "k_dpmpp_sde", "ddim_v3"]],
           help_text="设置采样方式"),
    Option("--width", Args['width', int], help_text="设置宽度"),
    Option("--height", Args['height', int], help_text="设置高度"),
    Option("--scale", Args['scale', float], help_text="设置scale"),

    meta=CommandMeta(fuzzy_match=True,
                     usage="draw [prompt] [-neg negative_prompt] [-s seed] "
                           "[-cfg cfg_rescale] [-sam sampler] [-w width] [-h height]",
                     description="使用指定的prompt生成图片"
                     )
)

if __name__ == "__main__":
    print(DrawCommand.get_help())
    body = "aaaaa --negative_prompt aaaa --seed 123 --steps 20 --scale 50 --sampler k_dpmpp_2m --width 123 --height 123"
    if body.find(" -") != -1:
        # 将 - 之前的内容用括号包裹
        flag = body[body.find(" -"):]
        body = body[:body.find(" -")]
        body = f"'{body}'{flag}"
        message_text = f"/draw {body}"
    else:
        message_text = f"/draw '{body}'"
    print(message_text)
    command = DrawCommand.parse(message_text)
    # print(DrawCommand.get_help())
    print(command)
    print(command.all_matched_args)

    dov = DrawCommand.parse("/draw aaaaa -nefg aaaa -s 123 -st 123 -cfg 123 -sam k_dpmpp_2m -wi 123 -he 123")
    print(dov)
    print(dov.error_info)
