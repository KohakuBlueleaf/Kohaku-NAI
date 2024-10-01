import io
from traceback import format_exc

import discord

from kohaku_nai.dc_bot_modules.functions import make_summary, log_error_command
from kohaku_nai.dc_bot_modules import config
from kohaku_nai.utils import set_client, remote_gen, DEFAULT_ARGS, make_file_name


class NAIImageGen(discord.ui.View):
    def __init__(
        self,
        prefix: str,
        origin: discord.Interaction,
        prompt,
        neg_prompt,
        width,
        height,
        steps,
        scale,
        seed,
        images,
        priority,
    ):
        super().__init__()
        self.images = images
        self.origin = origin
        self.prefix = prefix
        self.generate_config = {
            "prompt": prompt,
            "quality_tags": True,
            "negative_prompt": neg_prompt,
            "ucpreset": "Heavy",
            "width": width,
            "height": height,
            "steps": steps,
            "scale": scale,
            "seed": seed,
            "sampler": "k_euler",
            "schedule": "native",
            "images": images,
            "priority": priority,
        }

    @discord.ui.select(
        placeholder="Quality Tags: Enable",
        options=[
            discord.SelectOption(label="Enable", value="Enable"),
            discord.SelectOption(label="Disable", value="Disable"),
        ],
    )
    async def quality_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        if select.values[0] == "Enable":
            self.generate_config["quality_tags"] = True
        else:
            self.generate_config["quality_tags"] = False
        select.placeholder = f"Quality Tags: {select.values[0]}"
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder="UC preset: Heavy",
        options=[
            discord.SelectOption(label="Heavy", value="Heavy"),
            discord.SelectOption(label="Light", value="Light"),
            discord.SelectOption(label="None", value="None"),
        ],
    )
    async def uc_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        self.generate_config["ucpreset"] = select.values[0]
        select.placeholder = f"UC preset: {select.values[0]}"
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder="Sampler: Euler",
        options=[
            discord.SelectOption(label="Euler", value="k_euler"),
            discord.SelectOption(label="Euler A", value="k_euler_ancestral"),
            discord.SelectOption(label="DPM++ 2S A", value="k_dpmpp_2s_ancestral"),
            discord.SelectOption(label="DPM++ 2M", value="k_dpmpp_2m"),
            discord.SelectOption(label="DPM++ SDE", value="k_dpmpp_sde"),
            discord.SelectOption(label="DDIM V3", value="ddim_v3"),
        ],
    )
    async def sampler_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        self.generate_config["sampler"] = select.values[0]
        select.placeholder = f"Sampler: {select.values[0]}"
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder="Scheduler: Native",
        options=[
            discord.SelectOption(label="Native", value="native"),
            discord.SelectOption(label="Karras", value="karras"),
            discord.SelectOption(label="Exponential", value="exponential"),
            discord.SelectOption(label="PolyExponential", value="polyexponential"),
        ],
    )
    async def schedule_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        self.generate_config["schedule"] = select.values[0]
        select.placeholder = f"Scheduler: {select.values[0]}"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Generate", style=discord.ButtonStyle.green)
    async def generate_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            gen_command = make_summary(self.generate_config, self.prefix, DEFAULT_ARGS)
            await self.origin.edit_original_response(
                content=f"### Generating with command:\nImages: (0/{self.images})\n{gen_command}",
                view=None,
                embed=None,
            )
            await interaction.response.defer(thinking=True)
            await set_client("httpx", config.GEN_SERVER_URL, config.GEN_SERVER_PSWD)

            imgs, infos = [], []
            for i in range(self.images):
                img, info = await remote_gen(
                    config.GEN_SERVER_URL,
                    extra_infos={"save_folder": "discord-bot"},
                    **self.generate_config,
                )
                imgs.append(img)
                infos.append(info)
                await self.origin.edit_original_response(
                    content=f"### Generating with command:\nImages: ({i+1}/{self.images})\n{gen_command}",
                    view=None,
                    embed=None,
                )

            if any(img is None for img in imgs):
                error_embed = discord.Embed(
                    title="Error", description="Failed to generate image"
                )
                for info, img in zip(infos, imgs):
                    if img is not None:
                        continue
                    if isinstance(info, dict):
                        for k, v in info.items():
                            error_embed.add_field(name=k, value=v)
                    else:
                        error_embed.add_field(name="info", value=str(info))
                await interaction.followup.send(
                    content=f"### Generation Failed:\n{gen_command}", embed=error_embed
                )

            if any(img is not None for img in imgs):
                await interaction.followup.send(
                    content=f"{interaction.user.mention}\n### Generation done:\n{gen_command}",
                    files=[
                        discord.File(
                            io.BytesIO(info),
                            filename=make_file_name(self.generate_config) + ".png",
                        )
                        for img, info in zip(imgs, infos)
                        if img is not None
                    ],
                )

            await self.origin.edit_original_response(
                content=f"### Generation done:\n{gen_command}"
            )
        except Exception as e:
            err = format_exc()
            log_error_command(err)
            raise e
