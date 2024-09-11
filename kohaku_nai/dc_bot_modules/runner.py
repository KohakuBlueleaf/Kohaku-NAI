import asyncio
import sys

from asyncio import run
from json import loads

import discord
from discord.ext import commands

from kohaku_nai.dc_bot_modules import config


print(sys.version_info)
intents = discord.Intents.all()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


cmd_config = loads(sys.argv[1])
config.GEN_SERVER_URL = cmd_config.get("url", config.GEN_SERVER_URL)
config.GEN_SERVER_PSWD = cmd_config.get("password", config.GEN_SERVER_PSWD)
config.GUILD_PRIORITY = {
    int(k): v
    for k, v in cmd_config.get("guild_priority", config.GUILD_PRIORITY).items()
}
config.USER_PRIORITY = {
    int(k): v 
    for k, v in cmd_config.get("user_priority", config.USER_PRIORITY).items()
}


async def main():
    global bot
    bot = commands.Bot(
        command_prefix=cmd_config["prefix"],
        description=cmd_config["description"],
        intents=intents if cmd_config["intents"] else None,
    )
    await bot.load_extension(cmd_config["extension_path"])
    await bot.start(cmd_config["token"])


run(main())
