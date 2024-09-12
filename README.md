# Kohaku-NAI

A simple Novel-AI client with some utilities built in it.

Also a stable-diffusion-webui extension.

**Sharing your account to your friends may violate the NAI's TOS. USE AT YOUR OWN RISK!!!**

### Demo for standalone client and SD-WebUI extension

| ![image](https://github.com/KohakuBlueleaf/Kohaku-NAI/assets/59680068/e7e853d3-cbe1-4082-8cf6-b395648f342b) | ![image](https://github.com/KohakuBlueleaf/Kohaku-NAI/assets/59680068/3ce65dff-68a7-4122-bec9-58c6bd4ade01) |
| --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |

### Demo for DC bot

https://github.com/KohakuBlueleaf/Kohaku-NAI/assets/59680068/3da2eca2-edc0-4caa-9d55-c68e563b9be8

## Features

* Generation Server with followed features.
  * saving images automatically
  * account pool
  * minimum delay between requests
  * request rate limit
  * Auth system
* Standalone Client which can connect to NAI directly or connect to the generation server.
* DC bot based on gen server.

## Usage

### sd-webui

You can treat this repo as a [a1111 sd-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) extensions.
Just put the repo url into `Extensions > Install from URL > URL for extension's git repository` and then click Install button.

**Remember to restart the sd-webui process.**

Once you restart your sd-webui, you can find a "Kohaku NAI Client" option under the "Script" dropdown in `Txt 2 Img` tab. And a `Kohaku-NAI` section in the `settings` tab.

Put your token (or generation server's url) into settings, save them. And then choose "Kohaku NAI Client" option in the "Script" dropdown. Now you can generate images with NAI api within sd-webui.

---

### Setup for standalone usage or gen-server or cli or dc bot

```
git clone https://github.com/KohakuBlueleaf/Kohaku-NAI.git
cd Kohaku-NAI
python -m venv venv
./venv/Scripts/activate
python -m pip install -r ./requirements.txt
```

---

### Standalone Gradio Client

If you just want to use it as a standalone client.
Just change the `mode` of the client section in the `config.toml` to `local` and put your NovelAI API token to `token`.

If you want to connect to others' generation servers, contact the server maintainer for endpoint url.
(If you are the server owner, check next section)

And then use `python -m kohaku_nai.gr_client` to run it.

---

### Standalone Client

`python -m kohaku_nai.cli_client --help` for more informations.

---

### Generation Server

Put your NAI token into `token` in the server section in the `config.toml`.

use `python -m kohaku_nai.server` to run it.

---

### DC bot

Check the example `dc-bot-config.json`. Change the token/prefix to your bot's. And the `url` and `passowrd` are for your gen-server.

And then run:

```
python -m kohaku_nai.dc_bot
```

---

## Future Plan

* Server
  * [X] QoS system (Should have dedicated QoS on dc bot side and give dc bot white list)
* Client
  - [ ] Better Client (maybe static website implemented in Vue)
  - [X] sd-webui extensions
  - [X] Discord bot
  - [X] CLI
* Utils
  - [ ] Random Prompts
  - [X] Wildcard [built-in extensions]
  - [ ] auto gen
* API
  - [ ] Fetch Account info (if possible?)

## Disclaimer

The Kohaku-NAI project, including its standalone gradio client, CLI client, gen server and stable-diffusion-webui extension for using NovelAI api conveniently, is provided "as is" without warranty of any kind, either expressed or implied. While every effort has been made to ensure the functionality and reliability of the software, the creators of Kohaku-NAI do not guarantee its absolute safety, efficiency, or compatibility with all systems.

Users should be aware that the use of Kohaku-NAI involves certain risks, including but not limited to:

* Potential violation of Novel-AI's Terms of Service if sharing accounts, hosting gen server as service or hosting dc bots as service. Users are responsible for adhering to all applicable terms and conditions set forth by Novel-AI.
* Possible software bugs or malfunctions, which may result in data loss or other damages. Users are advised to frequently back up their data when using Kohaku-NAI.
* Variability in the performance of the software depending on the user's hardware, software, and other technical configurations.

By using Kohaku-NAI, users acknowledge and agree that they are doing so at their own risk. The developers of Kohaku-NAI shall not be liable for any direct, indirect, incidental, special, consequential, or exemplary damages arising from the use or inability to use the software.

Users are encouraged to report any bugs or issues to the development team to help improve Kohaku-NAI. Feedback and contributions are always welcome.

This disclaimer is subject to changes and updates, and users are advised to review it periodically.
