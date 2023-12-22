# -*- coding: utf-8 -*-

import asyncio
import pathlib
from json import load

from loguru import logger

from kohaku_nai.tg_bot_modules.config import TgBotSettings
from tg_bot_modules.controller import BotRunner

CONFIG_FILE = pathlib.Path("tg-bot-config.json")
if not CONFIG_FILE.exists():
    raise FileNotFoundError(
        f"tg-bot-config.json not found, please make sure {CONFIG_FILE.absolute()} "
        f"exists? Make sure start from root directory..."
    )

try:
    with CONFIG_FILE.open("r") as f:
        config = load(f)
except Exception as e:
    logger.exception(f"Load config error: {e}")
    raise e

setting = TgBotSettings(**config)


async def main():
    await asyncio.gather(
        BotRunner().run(setting)
    )


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
