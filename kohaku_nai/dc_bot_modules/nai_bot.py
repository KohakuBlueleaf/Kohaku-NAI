import shlex
import io
from traceback import format_exc

import discord
import discord.ext.commands as dc_commands
from discord import app_commands
from discord.ext.commands import CommandNotFound, Context

from kohaku_nai.args_creator import CAPITAL_ARGS_MAPPING, parse_args
from kohaku_nai.dc_bot_modules.functions import make_summary, log_error_event, log_error_command
from kohaku_nai.dc_bot_modules.dc_views import NAIImageGen
from kohaku_nai.dc_bot_modules import config

from kohaku_nai.utils import set_client, remote_gen, DEFAULT_ARGS, make_file_name


INVALID_NOTICE = "Your input is invalid"


def event_with_error(func):
    async def function(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            err = format_exc()
            log_error_event(err)

    function.__name__ = func.__name__
    return function


class KohakuNai(dc_commands.Cog):
    def __init__(self, bot: dc_commands.Bot):
        self.bot = bot
        self.prefix = bot.command_prefix

    @dc_commands.Cog.listener()
    @event_with_error
    async def on_ready(self):
        print(f"Logged in as: {self.bot.user} (ID: {self.bot.user.id})")
        print(f"Command prefix is: {self.prefix}")
        print("Guilds:")
        for guild in self.bot.guilds:
            print(f"- {guild.name} (ID: {guild.id})")

        await self.bot.change_presence(
            status=discord.Status.online, activity=discord.Game("Novel AI UwU")
        )
        print("------")

    @dc_commands.Cog.listener(name="on_error")
    async def on_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        try:
            raise error
        except Exception:
            err = format_exc()
            log_error_command(err)

    @dc_commands.command()
    async def sync_command_tree(self, ctx: Context):
        if ctx.author.guild_permissions.administrator:
            await self.bot.tree.sync()
            await ctx.send("Command tree synced")

    @dc_commands.command(pass_context=True)
    async def novelai(self, ctx: Context, *, message: str):
        user = ctx.author
        guild = ctx.guild
        user_priority = config.USER_PRIORITY.get(user.id, 0)
        guild_priority = 0
        if guild is not None:
            guild_priority = config.GUILD_PRIORITY.get(guild.id, 0)
        priority = max(guild_priority, user_priority)

        default_args = dict(DEFAULT_ARGS.items())
        args, kwargs = parse_args(message)
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
            images = int(default_args["images"])
        except ValueError:
            await ctx.reply(INVALID_NOTICE)
            return

        if (
            width % 64
            or height % 64
            or width * height > 1024 * 1024
            or steps > 28
            or scale < 0
            or images > 4
            or images < 1
        ):
            await ctx.reply(INVALID_NOTICE)
            return

        gen_command = make_summary(default_args, self.prefix, DEFAULT_ARGS)
        gen_message = await ctx.reply(
            content=f"### Generating with command:\nimages: (0/{images})\n{gen_command}"
        )
        async with ctx.typing():
            await set_client("httpx", config.GEN_SERVER_URL, config.GEN_SERVER_PSWD)
            imgs, infos = [], []
            for i in range(images):
                img, info = await remote_gen(
                    config.GEN_SERVER_URL,
                    extra_infos={"save_folder": "discord-bot"},
                    **default_args,
                    priority=priority,
                )
                imgs.append(img)
                infos.append(info)
                await gen_message.edit(
                    content=f"### Generating with command:\nimages: ({i+1}/{images})\n{gen_command}"
                )

        try:
            if any(img is None for img in imgs):
                error_embed = discord.Embed(
                    title="Error", description="Failed to generate image"
                )
                for info, img in zip(infos, imgs):
                    if img is not None:
                        continue
                    if isinstance(info, dict):
                        for k, v in info.items():
                            error_embed.add_field(name=k, value=str(v)[:200] + "...")
                    else:
                        error_embed.add_field(
                            name="info", value=str(info)[:200] + "..."
                        )
                await ctx.reply(
                    content=f"{ctx.author.mention}\nGeneration failed:",
                    embed=error_embed,
                )

            if any(img is not None for img in imgs):
                await ctx.reply(
                    content=f"{ctx.author.mention}\nGeneration done:",
                    files=[
                        discord.File(
                            io.BytesIO(info),
                            filename=make_file_name(default_args) + ".png",
                        )
                        for img, info in zip(imgs, infos)
                        if img is not None
                    ],
                )
            await gen_message.delete()
        except Exception as e:
            err = format_exc()
            log_error_command(err)
            raise e

    @app_commands.command(name="nai", description="Use Novel AI to generate Images")
    async def nai(
        self,
        interaction: discord.Interaction,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 28,
        cfg_scale: float = 5.0,
        seed: int = -1,
        images: int = 1,
    ):
        if (
            width % 64
            or height % 64
            or width * height > 1024 * 1024
            or steps > 28
            or cfg_scale < 0
            or images > 4
            or images < 1
        ):
            await interaction.response.send_message(
                INVALID_NOTICE, ephemeral=True
            )
            return
        guild = interaction.guild
        user = interaction.user
        user_priority = config.USER_PRIORITY.get(user.id, 0)
        guild_priority = 0
        if guild is not None:
            guild_priority = config.GUILD_PRIORITY.get(guild.id, 0)
        priority = max(guild_priority, user_priority)
        embed = discord.Embed(title="Generation settings", color=0x50A4FF)
        embed.add_field(name="prompt", value=prompt, inline=False)
        embed.add_field(name="negative_prompt", value=negative_prompt, inline=False)
        embed.add_field(name="width", value=width, inline=False)
        embed.add_field(name="height", value=height, inline=False)
        embed.add_field(name="steps", value=steps, inline=False)
        embed.add_field(name="CFG scale", value=cfg_scale, inline=False)
        embed.add_field(name="Num of image gen", value=images, inline=False)
        await interaction.response.send_message(
            embed=embed,
            view=NAIImageGen(
                prefix=self.prefix,
                origin=interaction,
                prompt=prompt,
                neg_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                scale=cfg_scale,
                seed=seed,
                images=images,
                priority=priority,
            ),
            ephemeral=True,
        )


async def setup(bot: dc_commands.Bot):
    @bot.event
    async def on_message(message: discord.Message):
        if message.author.id == bot.user.id:
            return
        ctx = await bot.get_context(message)
        await bot.invoke(ctx)

    await bot.add_cog(KohakuNai(bot))
