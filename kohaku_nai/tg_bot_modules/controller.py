# -*- coding: utf-8 -*-
# @Time    : 2023/12/22 下午11:28
# @Author  : sudoskys
# @File    : controller.py
# @Software: PyCharm
import io

from loguru import logger
from telebot import types
from telebot import util, formatting
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

from kohaku_nai.args_creator import CAPITAL_ARGS_MAPPING, parse_args
from kohaku_nai.tg_bot_modules.config import TgBotSettings
from kohaku_nai.tg_bot_modules.functions import parse_command
from kohaku_nai.utils import DEFAULT_ARGS, set_client, remote_gen

StepCache = StateMemoryStorage()


class BotRunner(object):

    def run(self, setting: TgBotSettings):
        logger.info("Bot Start")
        bot = AsyncTeleBot(setting.token, state_storage=StepCache)
        if setting.proxy:
            from telebot import asyncio_helper
            asyncio_helper.proxy = setting.proxy
            logger.info("Proxy tunnels are being used!")

        @bot.message_handler(commands='help', chat_types=['private', 'supergroup', 'group'])
        async def listen_help_command(message: types.Message):
            _message = await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🥕 Help"),
                    formatting.mitalic("draw [prompt] [-neg negative_prompt] [-s seed] [-st steps] "
                                       "[-cfg cfg_rescale] [-sam sampler] [-wi width] [-he height]"
                                       ),
                    formatting.mbold("🥕 /draw"),
                ),
                parse_mode="MarkdownV2"
            )

        @bot.message_handler(
            commands='draw',
            content_types=["text"],
            chat_types=['group', 'supergroup', 'private']
        )
        async def listen_draw_command(message: types.Message):
            """
            群组命令，draw something
            :param message:
            :return:
            """
            message_text = message.text if message.text else message.caption
            # 参数内容
            head, body = parse_command(message_text)
            if not body:
                return await bot.reply_to(
                    message,
                    "🥕 Input something to draw!"
                )
            # 解析参数
            default_args = dict(DEFAULT_ARGS.items())
            args, kwargs = parse_args(body)
            for k in list(kwargs):
                if k in CAPITAL_ARGS_MAPPING:
                    kwargs[CAPITAL_ARGS_MAPPING[k]] = kwargs.pop(k)
            for k in list(default_args):
                if k in kwargs:
                    default_args[k] = kwargs[k]
                elif args:
                    default_args[k] = args.pop(0)
            try:
                width = int(default_args["width"])
                height = int(default_args["height"])
                steps = int(default_args["steps"])
                scale = float(default_args["scale"])
            except Exception:
                return await bot.reply_to(message, "Your input is invalid")

            if (
                    width % 64
                    or height % 64
                    or width * height > 1024 * 1024
                    or steps > 28
                    or scale < 0
            ):
                await bot.reply_to(message, "Your input is invalid")
                return

            logger.info(f"Generating with:\n{default_args}")
            await bot.send_chat_action(message.chat.id, "typing")
            try:
                await set_client("httpx", setting.url, setting.password)
                img, info = await remote_gen(
                    setting.url,
                    extra_infos={"save_folder": "telegram-bot"},
                    **default_args,
                )
                assert img is not None
            except Exception as e:
                logger.exception(e)
                return await bot.reply_to(message, "🥕 Generation failed")
            else:
                return await bot.send_document(
                    chat_id=message.chat.id,
                    document=(io.BytesIO(img), str(default_args) + ".png"),
                    caption=None,
                    reply_to_message_id=message.message_id,
                    parse_mode="MarkdownV2"
                )

        bot.polling(non_stop=True, allowed_updates=util.update_types, skip_pending=True)
