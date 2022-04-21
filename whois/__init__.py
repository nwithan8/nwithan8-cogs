from .whois import WhoIs


def setup(bot):
    bot.add_cog(WhoIs(bot))
