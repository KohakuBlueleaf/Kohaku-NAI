import random
import shlex
import io
from traceback import format_exc

import discord
import discord.ext.commands as dc_commands
from discord import app_commands
from discord.ext.commands import CommandNotFound, Context

from PIL import Image

from .functions import *
from .dc_views import NAIImageGen
from utils import remote_login, remote_gen, DEFAULT_ARGS


CAPITAL_ARGS_MAPPING = {
    'H': 'height',
    'W': 'width',
    'P': 'prompt',
    'N': 'neg_prompt',
    'S': 'seed',
    'UC': 'ucpreset',
    'QU': 'quality_tags',
}


def event_with_error(func):
    async def function(*args,**kwargs):
        try:
            return (await func(*args, **kwargs))
        except:
            err = format_exc()
            log_error_event(err)
    function.__name__ = func.__name__
    return function


def parse_args(message):
    opts = shlex.split(message)
    args = []
    kwargs = {}
    skip_next = False
    for k, v in zip(opts, opts[1:]+["--"]):
        if skip_next:
            skip_next = False
            continue
        if k.startswith('-'):
            if v.startswith('-'):
                kwargs[k.strip('-')] = True
            else:
                kwargs[k.strip('-')] = v
                skip_next = True
        else:
            args.append(k)
    return args, kwargs


class KohakuNai(dc_commands.Cog):
    def __init__(self, bot: dc_commands.Bot):
        self.bot = bot
        self.prefix = bot.command_prefix

    @dc_commands.Cog.listener()
    @event_with_error
    async def on_ready(self):
        print('Logged in as')
        print(self.bot.user.name)
        print(self.bot.user.id)
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game("Novel AI UwU"))
        print('------')

    @dc_commands.Cog.listener()
    @event_with_error
    async def on_command_error(self, ctx, error):
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
        gen_command = make_summary(default_args, self.prefix)
        gen_message = await ctx.reply(content=f"### Generating with command:\n{gen_command}", ephemeral=True)
        await ctx.message.delete()
        async with ctx.typing():
            await remote_login('http://127.0.0.1', '12345')
            img, info = await remote_gen(
                'http://127.0.0.1',
                extra_infos={'save_folder': 'discord-bot'},
                **default_args
            )
            if img is None:
                error_embed = discord.Embed(title="Error", description="Failed to generate image")
                if isinstance(info, dict):
                    for k, v in info.items():
                        error_embed.add_field(name=k, value=v)
                else:
                    error_embed.add_field(name="info", value=str(info))
                await gen_message.reply(embed=error_embed)
            else:
                await gen_message.reply(
                    content=ctx.author.mention,
                    file=discord.File(
                        io.BytesIO(info),
                        filename=str(default_args) + ".png"
                    )
                )
            await gen_message.edit(
                content = f'### Generation done:\n{gen_command}'
            )
    
    @app_commands.command(name="nai", description='Use Novel AI to generate Images')
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
    ):
        try:
            if width%64 or height%64 or width*height > 1024*1024 or steps>28:
                await interaction.response.send_message(
                    "你的設定有問題喔UwU(超出免費額度/非法數值)"
                )
                return
            if seed < 0:
                seed = random.randint(0, 2**32 - 1)
            embed = discord.Embed(title="生成設定", color=0x50A4ff)
            embed.add_field(name='prompt', value=prompt, inline=False)
            embed.add_field(name='negative_prompt', value=negative_prompt, inline=False)
            embed.add_field(name='width', value=width, inline=False)
            embed.add_field(name='height', value=height, inline=False)
            embed.add_field(name='steps', value=steps, inline=False)
            embed.add_field(name='CFG scale', value=cfg_scale, inline=False)
            await interaction.response.send_message(
                embed=embed,
                view=NAIImageGen(
                    prefix = self.prefix,
                    origin = interaction,
                    prompt=prompt,
                    neg_prompt=negative_prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    scale=cfg_scale,
                    seed=seed
                ), 
                ephemeral=True
            )
        except Exception:
            err = format_exc()
            log_error_command(err)


async def setup(bot: dc_commands.Bot):
    @bot.event
    async def on_message(message: discord.Message):
        if message.author.id == bot.user.id:
            return
        ctx = await bot.get_context(message)
        await bot.invoke(ctx)
    await bot.add_cog(KohakuNai(bot))