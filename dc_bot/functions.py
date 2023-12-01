CAPITAL_ARGS_MAPPING = {
    "H": "height",
    "W": "width",
    "P": "prompt",
    "N": "negative_prompt",
    "S": "seed",
    "UC": "ucpreset",
    "QU": "quality_tags",
}
ARGS_CAPITAL_MAPPING = {v: k for k, v in CAPITAL_ARGS_MAPPING.items()}


def make_summary(generate_config, prefix, default=None):
    config = dict(generate_config.items())
    if default is None:
        default = {}

    summary = f'{prefix}novelai "{config.pop("prompt", "")}" '
    if config["negative_prompt"]:
        summary += f'"{config.pop("negative_prompt", "")}" '
    if config.pop("quality_tags", False):
        summary += "-QU "

    for k, v in config.items():
        if k in default and v == default[k]:
            continue
        if k in ARGS_CAPITAL_MAPPING:
            k = ARGS_CAPITAL_MAPPING[k]
            summary += f"-{k}"
        else:
            summary += f"--{k}"
        summary += f" {v} "
    return f"```\n{summary}\n```"


"""
Error logging
"""


def log_error_command(err):
    errors = err.split("\n\n")[0].strip().split("\n")
    if errors[1][-10:] == "in wrapped":
        line = 3
    else:
        line = 1

    err_file, err_line, err_pos = errors[line].strip().split(", ")
    err_program = errors[line + 1].strip()
    err_cls, err_mes = errors[-1].split(": ", 1)
    print(
        "====Error Occured====\n",
        "Error File   : {}\n".format(err_file.split()[-1]),
        "Error Line   : {}\n".format(err_line.split()[-1]),
        "Error Pos    : {}\n".format(err_pos.split()[-1]),
        "Error program: {}\n".format(err_program),
        "Error Class  : {}\n".format(err_cls),
        "Error Message: {}\n".format(err_mes),
        "=====================",
        sep="",
    )


def log_error_event(err):
    errors = err.split("\n\n")[0].strip().split("\n")

    err_file, err_line, err_pos = errors[-3].strip().split(", ")
    err_program = errors[-2].strip()
    err_cls, err_mes = errors[-1].split(": ", 1)
    print(
        "====Error Occured====\n",
        "Error File   : {}\n".format(err_file.split()[-1]),
        "Error Line   : {}\n".format(err_line.split()[-1]),
        "Error Pos    : {}\n".format(err_pos.split()[-1]),
        "Error program: {}\n".format(err_program),
        "Error Class  : {}\n".format(err_cls),
        "Error Message: {}\n".format(err_mes),
        "=====================",
        sep="",
    )
