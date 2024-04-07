import os
import re
from random import choice

from kohaku_nai.client_modules.extension import Extension, register_extension, basedir


wildcard_format = re.compile(r"__([^_]+)__")
wildcard_folder = os.path.join(basedir(), "wildcards")


def replace(match):
    key = match.group(1)
    return resolve_wildcard(key)


def resolve_wildcard(key):
    if "__" in key:
        nested_match = wildcard_format.search(key)
        if nested_match:
            nested_key = nested_match.group(1)
            nested_value = get_wildcard_value(nested_key)
            if nested_value:
                key = key.replace(f"__{nested_key}__", nested_value)
                return resolve_wildcard(key)
    return get_wildcard_value(key) or key


def get_wildcard_value(key):
    for file in os.listdir(wildcard_folder):
        if file.startswith(key):
            with open(os.path.join(wildcard_folder, file), "r", encoding="utf-8") as f:
                lines = f.readlines()
                return choice(lines).strip()
    return None


class WildcardExtension(Extension):
    def process_prompt(self, prompt):
        return wildcard_format.sub(replace, prompt)


register_extension(WildcardExtension())
