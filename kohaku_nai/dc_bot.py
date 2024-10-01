from subprocess import Popen
from json import load, dumps
from time import sleep


with open("./dc-bot-config.json", "r", encoding="utf-8") as f:
    bots_config = load(f)


p_list = []
for config in bots_config["test_bots"]:
    config_str = dumps(config, ensure_ascii=False)
    if bots_config.get("pyinstaller", False):
        p_list.append(Popen([bots_config["pyinstaller-script"], config_str]))
    else:
        p_list.append(
            Popen(
                [
                    bots_config["python-script"],
                    "-m",
                    "kohaku_nai.dc_bot_modules.runner",
                    config_str,
                ]
            )
        )


input()


for process in p_list:
    process.terminate()
    while not process.poll():
        sleep(0.01)
