import os
import re
from random import choice

from kohaku_nai.client_modules.extension import Extension, register_extension, basedir


wildcard_format = re.compile(r"__([^_]+)__")
wildcard_folder = os.path.join(basedir(), "wildcards")


class WildcardExtension(Extension):
    def process_prompt(self, prompt):
        if prompt.strip() == "":
            return prompt

        def replace(match):
            key = match.group(1)

            for file in os.listdir(wildcard_folder):
                if file.startswith(key):
                    break
            else:
                return f"__{key}__"

            with open(os.path.join(wildcard_folder, file), "r", encoding="utf-8") as f:
                lines = f.readlines()

            return choice(lines).strip()

        return wildcard_format.sub(replace, prompt)


register_extension(WildcardExtension())
