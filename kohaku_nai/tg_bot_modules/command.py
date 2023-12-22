# -*- coding: utf-8 -*-


from typing import Annotated

from arclet.alconna import Alconna, Args, Option, CommandMeta

DrawCommand = Alconna(
    "/draw",
    Args['prompt', str],
    Option("--negative_prompt", Args.negative_prompt[str], help_text="Set Negative Prompt"),
    Option("--seed", Args['seed', int], help_text="Set Seed Of Generation"),
    Option("--steps", Args['steps', Annotated[int, lambda x: x < 70]], help_text="Set Steps Of Generation"),
    Option("--scale", Args['scale', int], help_text="Set Scale Of Generation"),
    Option("--sampler", Args[
        "sampler", ["k_euler", "k_euler_ancestral", "k_dpmpp_2s_ancestral", "k_dpmpp_2m", "k_dpmpp_sde", "ddim_v3"]],
           help_text="Set Sampler"),
    Option("--width", Args['width', int], help_text="Set Width Of Picture"),
    Option("--height", Args['height', int], help_text="Set Height Of Picture"),
    Option("--scale", Args['scale', float], help_text="Set Scale Of Generation"),

    meta=CommandMeta(fuzzy_match=True,
                     usage="draw [prompt] [--negative_prompt negative_prompt] [--seed seed] [--steps steps] [--scale scale] [--sampler sampler] [--width width] [--height height]",
                     description="Generate Picture From Input Prompt"
                     )
)

if __name__ == "__main__":
    # HELP CASE
    print(DrawCommand.get_help())
    body = "aaaaa --negative_prompt aaaa --seed 123 --steps 20 --scale 50 --sampler k_dpmpp_2m --width 123 --height 123"

    # GOOD CASE
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

    # BAD CASE
    dov = DrawCommand.parse("/draw aaaaa -nefg aaaa -s 123 -st 123 -cfg 123 -sam k_dpmpp_2m -wi 123 -he 123")
    print(dov)
    print(dov.error_info)
