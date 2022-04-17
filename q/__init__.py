from .queue import Queue


def setup(bot):
    bot.add_cog(Queue(bot))
