import os
import importlib
import importlib.util


class Extension:
    def process_prompt(self, prompt):
        return prompt


def process_prompt(prompt):
    for ext in extensions:
        prompt = ext.process_prompt(prompt)
    return prompt


def register_extension(ext):
    extensions.append(ext)


def basedir():
    return current_basedir


def load_extensions(path="./client_extensions"):
    global current_basedir
    if not os.path.isdir(path):
        return

    for folder in os.listdir(path):
        folder_path = os.path.join(path, folder)
        scripts_path = os.path.join(folder_path, "scripts")
        current_basedir = folder_path
        if os.path.isdir(scripts_path):
            for file in os.listdir(scripts_path):
                if not file.endswith(".py"):
                    continue
                module_name = file[:-3]
                if module_name in extension_modules:
                    print(
                        f'Override loaded module "{module_name}" from "{scripts_path}"'
                    )

                spec = importlib.util.spec_from_file_location(
                    module_name, f"{scripts_path}/{file}"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                extension_modules[module_name] = module


## share vars
extensions: list[Extension] = []
extension_modules = {}
current_basedir = ""
