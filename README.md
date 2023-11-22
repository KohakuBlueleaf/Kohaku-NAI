# Kohaku-NAI[WIP]
A simple Novel-AI client with more utilities built in it

**Sharing your account to your friends may violate the NAI's TOS. USE AT YOUR OWN RISK!!!**

![image](https://github.com/KohakuBlueleaf/Kohaku-NAI/assets/59680068/8d679565-a578-4c50-8e97-fcedf77f4271)

## Features
* Generation Server for managing manual rate limit and saving the images automatically.
* Standalone Client which can connect to NAI directly or connect to the generation server.

## Usage

### Setup
```
git clone https://github.com/KohakuBlueleaf/Kohaku-NAI.git
cd Kohaku-NAI
python -m pip install -r ./requirements.txt
```

### Client
If you just want to use it as a standalone client.
Just change the `mode` of the client section in the `config.toml` to `local` and put your NovelAI API token to `token`.

If you want to connect to others' generation servers, contact the server maintainer for endpoint url.
(If you are the server owner, check next section)

And then use `python ./gr_client.py` to run it.

### Server
Put your NAI token into `token` in the server section in the `config.toml`.

use `python ./gen_server.py` to run it.

You can also use uvicorn to deploy it:
```
uvicorn gen_server:app
```