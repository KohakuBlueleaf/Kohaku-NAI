import asyncio
import os,sys
print(sys.version_info)
from asyncio import run
from json import loads

import discord
intents = discord.Intents.all()
from discord.ext import commands

from . import config

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


cmd_config = loads(sys.argv[1])
config.GEN_SERVER_URL = cmd_config.get('url', config.GEN_SERVER_URL)
config.GEN_SERVER_PSWD = cmd_config.get('password', config.GEN_SERVER_PSWD)
async def main():
    global bot
    bot = commands.Bot(
        command_prefix=cmd_config['prefix'], 
        description=cmd_config['description'], 
        intents = intents if cmd_config['intents'] else None
    )
    await bot.load_extension(cmd_config['extension_path'])
    await bot.start(cmd_config['token'])


run(main())