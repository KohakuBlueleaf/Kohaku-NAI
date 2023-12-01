# Kohaku-NAI
A simple Novel-AI client with some utilities built in it.

Also a stable-diffusion-webui extension.

**Sharing your account to your friends may violate the NAI's TOS. USE AT YOUR OWN RISK!!!**

### Demo for standalone client and SD-WebUI extension
|![image](https://github.com/KohakuBlueleaf/Kohaku-NAI/assets/59680068/8d679565-a578-4c50-8e97-fcedf77f4271)|![image](https://github.com/KohakuBlueleaf/Kohaku-NAI/assets/59680068/3ce65dff-68a7-4122-bec9-58c6bd4ade01)|
| --- | ---|

### Demo for DC bot
https://github.com/KohakuBlueleaf/Kohaku-NAI/assets/59680068/3da2eca2-edc0-4caa-9d55-c68e563b9be8


## Features
* Generation Server for managing manual rate limit and saving the images automatically.
* Standalone Client which can connect to NAI directly or connect to the generation server.
* DC bot based on gen server.

## Usage

### sd-webui
You can treat this repo as a [a1111 sd-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) extensions.
Just put the repo url into `Extensions > Install from URL > URL for extension's git repository` and then click Install button.

**Remember to restart the sd-webui process.**

Once you restart your sd-webui, you can find a "Kohaku NAI Client" option under the "Script" dropdown in `Txt 2 Img` tab. And a `Kohaku-NAI` section in the `settings` tab.

Put your token (or generation server's url) into settings, save them. And then choose "Kohaku NAI Client" option in the "Script" dropdown. Now you can generate images with NAI api within sd-webui.

### Setup for standalone usage or gen-server
```
git clone https://github.com/KohakuBlueleaf/Kohaku-NAI.git
cd Kohaku-NAI
python -m pip install -r ./requirements.txt
```

### Standalone Client
If you just want to use it as a standalone client.
Just change the `mode` of the client section in the `config.toml` to `local` and put your NovelAI API token to `token`.

If you want to connect to others' generation servers, contact the server maintainer for endpoint url.
(If you are the server owner, check next section)

And then use `python ./gr_client.py` to run it.

### Generation Server
Put your NAI token into `token` in the server section in the `config.toml`.

use `python ./gen_server.py` to run it.

You can also use uvicorn to deploy it:
```
uvicorn gen_server:app
```

### DC bot
**experimental, coding skill are required for use it at this time**

For now, dc bot's config for gen server is hard coded.
If you want to use it, change the content in the dc-bot-config.json

And then find the url/password in `dc_bot/dc_views.py` and `dc_bot/nai_bot.py`. Change them into your url.

(Due to the property of DC bot, I have no plan to add "local gen" for it. Start to use gen server!)


## Future Plan
* Client
    - [ ] Better Client (maybe static website implemented in Vue)
    - [x] sd-webui extensions
    - [x] Discord bot 
* Utils
    - [ ] Random Prompts
    - [x] Wildcard [built-in extensions]
    - [ ] auto gen
* API
    - [ ] Fetch Account info (if possible?)
