import discord
import owowen
from redbot.core import commands, checks
from redbot.core.utils.mod import is_mod_or_superior
from redbot.core import Config
from redbot.core.commands import Context

from n8cog import BaseCog
from wow.identifier import IDENTIFIER
import urllib.request

__version__ = "1.0.0"


def _download_wow_video(link: str) -> bool:
    try:
        urllib.request.urlretrieve(link, "wow.mp4")
        return True
    except Exception as e:
        return False


class Wow(BaseCog):
    """Wow"""

    def __init__(self, bot: commands.Bot):
        super().__init__(name="Wow", bot=bot)

    @commands.guild_only()
    @commands.command(name="wow")
    async def wow(self, ctx):
        """
        Wow
        """
        api = owowen.API()
        wow = api.get_random_wow(count=1)
        if not wow:
            return await ctx.send("Something went wrong. Not wow.")
        if not _download_wow_video(wow[0].video.link_720p):
            return await ctx.send("Something went wrong. Not wow.")
        await ctx.send(file=discord.File(f"wow.mp4"))
