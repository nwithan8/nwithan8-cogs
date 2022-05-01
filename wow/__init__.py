from .wow import Wow


def setup(bot):
    bot.add_cog(Wow(bot))
