import os
import re
from random import choice

from kohaku_nai.client_modules.extension import Extension, register_extension, basedir

wildcard_format = re.compile(r"__([^_]+)__")
wildcard_folder = os.path.join(basedir(), "wildcards")

class WildcardExtension(Extension):
    def process_prompt(self, prompt):
        def replace(match):
            key = match.group(1)
            while True:
                if "__" in key:
                    nested_match = wildcard_format.search(key)
                    if nested_match:
                        nested_key = nested_match.group(1)
                        for file in os.listdir(wildcard_folder):
                            if file.startswith(nested_key):
                                with open(os.path.join(wildcard_folder, file), "r", encoding="utf-8") as f:
                                    lines = f.readlines()
                                    line = choice(lines).strip()
                                    key = key.replace(f"__{nested_key}__", line)
                                    break
                        else:
                            break
                    else:
                        break
                else:
                    for file in os.listdir(wildcard_folder):
                        if file.startswith(key):
                            with open(os.path.join(wildcard_folder, file), "r", encoding="utf-8") as f:
                                lines = f.readlines()
                                line = choice(lines).strip()
                                key = line
                                break
                    else:
                        break
            return f"{key}"

        return wildcard_format.sub(replace, prompt)

register_extension(WildcardExtension())
