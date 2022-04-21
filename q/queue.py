import discord
from redbot.core import commands, checks
from redbot.core.utils.mod import is_mod_or_superior
from redbot.core import Config
from redbot.core.commands import Context

from n8cog import BaseCog
from q.database import QueueDatabase, UserQueueEntry
from q.utils import int_to_place, get_guild_database, QueueType

IDENTIFIER = 551796800
__version__ = "1.0.0"


class Queue(BaseCog):
    """Queue cog"""

    def __init__(self, bot: commands.Bot):
        super().__init__(name="Q", bot=bot)

        self.config = Config.get_conf(self, identifier=IDENTIFIER, force_registration=True)

        default_guild = {
            "queue_types": []
        }

        self.config.register_guild(**default_guild)

    async def add_queue_type(self, ctx: Context, queue_type: QueueType) -> None:
        existing_queue_types = await self.config.guild(ctx.guild).queue_types()
        existing_queue_types.append(queue_type.string)
        await self.config.guild(ctx.guild).queue_types.set(existing_queue_types)
        await ctx.send("Queue type set up!")

    async def get_database(self, ctx: Context) -> QueueDatabase:
        guild_database_path = get_guild_database(guild=ctx.guild)
        queue_type_strings = await self.config.guild(ctx.guild).queue_types()
        schemas = []
        for queue_type_string in queue_type_strings:
            queue_type = QueueType.from_string(queue_type_string)
            if queue_type:
                schemas.append(queue_type.schema)
        return QueueDatabase(sqlite_file=guild_database_path, table_schemas=schemas)

    async def queue_set_up(self, ctx: Context, queue_type: QueueType) -> bool:
        return queue_type.string in await self.config.guild(ctx.guild).queue_types()

    async def database_pre_check(self, ctx: Context, queue_type: QueueType) -> bool:
        if not await self.queue_set_up(ctx=ctx, queue_type=queue_type):
            await ctx.send("Queue type is not set up!")
            return False
        return True

    @commands.guild_only()
    @commands.group(name="q")
    async def queue(self, ctx):
        pass

    @queue.command(name="new")
    @checks.admin_or_permissions(manage_guild=True)
    async def queue_new(self, ctx: Context, queue_type: str):
        """
        Creates a new q
        """
        queue_type_enum = QueueType.from_string(queue_type)
        if not queue_type_enum:
            await ctx.send("Invalid queue type!")
            return
        if queue_type_enum.string in await self.config.guild(ctx.guild).queue_types():
            await ctx.send("Queue type is already set up!")
            return
        await self.add_queue_type(ctx=ctx, queue_type=queue_type_enum)

    @queue.group(name="users")
    async def queue_users(self, ctx: Context):
        pass

    @queue_users.command(name="add")
    async def queue_users_add(self, ctx: Context):
        """
        Adds yourself to the q.
        """
        if await self.database_pre_check(ctx=ctx, queue_type=QueueType.USERS):
            user_id = ctx.author.id
            database = await self.get_database(ctx=ctx)
            if database.get_user_from_queue(user_id=user_id):
                await ctx.send("You are already in the queue!")
                return
            if database.add_user_to_queue(user_id=user_id):
                await ctx.send("You have been added to the queue!")
                return
            await self.send_error(ctx=ctx)

    @queue_users.command(name="remove")
    async def queue_users_remove(self, ctx: Context, user: discord.Member = None):
        """
        Remove yourself or another user from the q.
        """
        if await self.database_pre_check(ctx=ctx, queue_type=QueueType.USERS):
            database = await self.get_database(ctx=ctx)
            if user:
                if not await is_mod_or_superior(self.bot, ctx.author):
                    await self.send_error(ctx=ctx,
                                          error_message="You do not have permission to remove other users from the "
                                                        "queue!")
                    return
                user_id = user.id
                if not database.get_user_from_queue(user_id=user_id):
                    await ctx.send("That user is not in the queue!")
                    return
                database.delete_user_from_queue(user_id=user_id)  # always returns true
                await ctx.send(f"<@{user_id}> has been removed from the queue!")
            else:
                user_id = ctx.author.id
                if not database.get_user_from_queue(user_id=user_id):
                    await ctx.send("You are not in the queue!")
                    return
                database.delete_user_from_queue(user_id=user_id)  # always returns true
                await ctx.send(f"You has been removed from the queue!")

    @queue_users.command(name="place")
    async def queue_users_place(self, ctx: Context):
        """
        See where you are in the q
        """
        if await self.database_pre_check(ctx=ctx, queue_type=QueueType.USERS):
            database = await self.get_database(ctx=ctx)
            user_id = ctx.author.id
            user_location = database.find_user_location_in_queue(user_id=user_id)
            if not user_location:
                await ctx.send("You are not in the queue!")
                return
            await ctx.send(f"You are currently {int_to_place(user_location)} in the queue!")

    @queue_users.command(name="next")
    @checks.admin_or_permissions(manage_guild=True)
    async def queue_users_next(self, ctx: Context):
        """
        See who is next in the q
        """
        if await self.database_pre_check(ctx=ctx, queue_type=QueueType.USERS):
            database = await self.get_database(ctx=ctx)
            next_user = database.get_next_user_from_queue()
            if not next_user:
                await ctx.send("There is no one in the queue!")
                return
            await ctx.send(f"The next user in the queue is <@{next_user.user_id}>!")

    @queue_users.command(name="export")
    @checks.admin_or_permissions(manage_guild=True)
    async def queue_users_export(self, ctx: Context):
        """
        Export the queue to a CSV.
        """
        if await self.database_pre_check(ctx=ctx, queue_type=QueueType.USERS):
            database = await self.get_database(ctx=ctx)
            if not database.export_user_queue_to_csv(f"{ctx.guild.id}_user_queue.csv"):
                await self.send_error(ctx=ctx)
                return
            await ctx.send(file=discord.File(f"{ctx.guild.id}_user_queue.csv"))
