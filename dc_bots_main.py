from subprocess import Popen
from json import load, dumps


with open('./dc-bot-config.json','r',encoding='utf-8') as f:
    bots_config = load(f)


p_list = []
for config in bots_config['test_bots']:
    config_str = dumps(config, ensure_ascii=False)
    p_list.append(Popen([bots_config['python-script'], '-m', 'dc_bot.runner', config_str]))


input()


for process in p_list:
    process.terminate()
    while not process.poll():
        pass