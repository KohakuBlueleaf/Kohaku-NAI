import asyncio
import os,sys
print(sys.version_info)
from asyncio import run
from json import loads

import discord
intents = discord.Intents.all()
from discord.ext import commands

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


config = loads(sys.argv[1])
async def main():
    global bot
    bot = commands.Bot(
        command_prefix=config['prefix'], 
        description=config['description'], 
        intents = intents if config['intents'] else None
    )
    await bot.load_extension(config['extension_path'])
    await bot.start(config['token'])


run(main())