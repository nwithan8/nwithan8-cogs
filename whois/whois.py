import discord
from redbot.core import commands, checks
from redbot.core.utils.mod import is_mod_or_superior
from redbot.core import Config
from redbot.core.commands import Context

from n8cog import BaseCog

IDENTIFIER = 551796800
__version__ = "1.0.0"


class WhoIs(BaseCog):
    """Find out who people are."""

    def __init__(self, bot: commands.Bot):
        super().__init__(name="WhoIs", bot=bot)

    @commands.guild_only()
    @commands.group(name="whois")
    async def whois(self, ctx):
        pass

    @whois.command(name="discord")
    async def whois_discord(self, ctx: Context, user_id: int):
        """
        Find out what user has this Discord ID
        """
        try:
            user = await self.bot.fetch_user(user_id)
            if user is None:
                await ctx.reply("User not found.")
                return
            await ctx.reply(f"{user_id} -> <@{user_id}>")
        except Exception as e:
            await ctx.reply(f"User not found.")
