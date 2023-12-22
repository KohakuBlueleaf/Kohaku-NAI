# -*- coding: utf-8 -*-

import shlex

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


def parse_args(message: str):
    opts = shlex.split(message)
    args = []
    kwargs = {}
    skip_next = False
    for k, v in zip(opts, opts[1:] + ["--"]):
        if skip_next:
            skip_next = False
            continue
        if k.startswith("-"):
            if v.startswith("-"):
                kwargs[k.strip("-")] = True
            else:
                kwargs[k.strip("-")] = v
                skip_next = True
        else:
            args.append(k)
    return args, kwargs
