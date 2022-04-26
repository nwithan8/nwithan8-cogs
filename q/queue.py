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
            "queue_names_and_types": {}
        }

        self.config.register_guild(**default_guild)

    async def add_queue(self, ctx: Context, queue_name: str, queue_type: QueueType) -> None:
        existing_queue_settings = await self.config.guild(ctx.guild).queue_names_and_types()
        existing_queue_settings[queue_name] = queue_type.string
        await self.config.guild(ctx.guild).queue_names_and_types.set(existing_queue_settings)
        await ctx.send(f"{queue_type.string} queue ``{queue_name}`` set up!")

    async def get_database(self, ctx: Context) -> QueueDatabase:
        guild_database_path = get_guild_database(guild=ctx.guild)
        queue_settings = await self.config.guild(ctx.guild).queue_names_and_types()
        schemas = []
        for queue_name, queue_type_string in queue_settings.items():
            queue_type = QueueType.from_string(queue_type_string)
            if queue_type and queue_type not in schemas:
                schemas.append(queue_type.schema)
        return QueueDatabase(sqlite_file=guild_database_path, table_schemas=schemas)

    async def queue_set_up(self, ctx: Context, queue_name: str, queue_type: QueueType) -> bool:
        settings = await self.config.guild(ctx.guild).queue_names_and_types()
        return queue_name in settings.keys() and settings[queue_name] == queue_type.string

    async def database_pre_check(self, ctx: Context, queue_name: str, queue_type: QueueType) -> bool:
        if not await self.queue_set_up(ctx=ctx, queue_name=queue_name, queue_type=queue_type):
            await ctx.send(f"{queue_type.string} queue ``{queue_name}`` is not set up!")
            return False
        return True

    async def create_new_queue(self, ctx: Context, queue_name: str, queue_type: QueueType) -> None:
        if await self.queue_set_up(ctx=ctx, queue_name=queue_name, queue_type=queue_type):
            await ctx.send(f"{queue_type.string} queue `{queue_name}` is already set up!")
            return
        await self.add_queue(ctx=ctx, queue_name=queue_name, queue_type=queue_type)

    @commands.guild_only()
    @commands.group(name="q")
    async def queue(self, ctx):
        pass

    @queue.group(name="users")
    async def queue_users(self, ctx: Context):
        pass

    @queue_users.command(name="new")
    async def queue_users_new(self, ctx: Context, queue_name: str):
        """
        Creates a new users queue
        """
        await self.create_new_queue(ctx=ctx, queue_name=queue_name, queue_type=QueueType.USERS)

    @queue_users.command(name="add")
    async def queue_users_add(self, ctx: Context, queue_name: str):
        """
        Adds yourself to the queue
        """
        if await self.database_pre_check(ctx=ctx, queue_name=queue_name, queue_type=QueueType.USERS):
            user_id = ctx.author.id
            database = await self.get_database(ctx=ctx)
            if database.get_user_from_queue(queue_name=queue_name, user_id=user_id):
                await ctx.send(f"You are already in the `{queue_name}` queue!")
                return
            if database.add_user_to_queue(queue_name=queue_name, user_id=user_id):
                await ctx.send(f"You have been added to the `{queue_name}` queue!")
                return
            await self.send_error(ctx=ctx)

    @queue_users.command(name="remove")
    async def queue_users_remove(self, ctx: Context, queue_name: str, user: discord.Member = None):
        """
        Remove yourself or another user from the queue
        """
        if await self.database_pre_check(ctx=ctx, queue_name=queue_name, queue_type=QueueType.USERS):
            database = await self.get_database(ctx=ctx)
            if user:
                if not await is_mod_or_superior(self.bot, ctx.author):
                    await self.send_error(ctx=ctx,
                                          error_message=f"You do not have permission to remove other users from the "
                                                        f"`{queue_name}` queue!")
                    return
                user_id = user.id
                if not database.get_user_from_queue(queue_name=queue_name, user_id=user_id):
                    await ctx.send(f"That user is not in the `{queue_name}` queue!")
                    return
                database.delete_user_from_queue(queue_name=queue_name, user_id=user_id)  # always returns true
                await ctx.send(f"<@{user_id}> has been removed from the `{queue_name}` queue!")
            else:
                user_id = ctx.author.id
                if not database.get_user_from_queue(queue_name=queue_name, user_id=user_id):
                    await ctx.send(f"You are not in the `{queue_name}` queue!")
                    return
                database.delete_user_from_queue(queue_name=queue_name, user_id=user_id)  # always returns true
                await ctx.send(f"You has been removed from the `{queue_name}` queue!")

    @queue_users.command(name="place")
    async def queue_users_place(self, ctx: Context, queue_name: str):
        """
        See where you are in the queue
        """
        if await self.database_pre_check(ctx=ctx, queue_name=queue_name, queue_type=QueueType.USERS):
            database = await self.get_database(ctx=ctx)
            user_id = ctx.author.id
            user_location = database.find_user_location_in_queue(queue_name=queue_name, user_id=user_id)
            if not user_location:
                await ctx.send(f"You are not in the `{queue_name}`queue!")
                return
            await ctx.send(f"You are currently {int_to_place(user_location)} in the `{queue_name}` queue!")

    @queue_users.command(name="next")
    @checks.admin_or_permissions(manage_guild=True)
    async def queue_users_next(self, ctx: Context, queue_name: str):
        """
        See who is next in the queue
        """
        if await self.database_pre_check(ctx=ctx, queue_name=queue_name, queue_type=QueueType.USERS):
            database = await self.get_database(ctx=ctx)
            next_user = database.get_next_user_from_queue(queue_name=queue_name)
            if not next_user:
                await ctx.send(f"There is no one in the `{queue_name}` queue!")
                return
            await ctx.send(f"The next user in the `{queue_name}` queue is <@{next_user.user_id}>!")

    @queue_users.command(name="export")
    @checks.admin_or_permissions(manage_guild=True)
    async def queue_users_export(self, ctx: Context):
        """
        Export all queues to a CSV.
        """
        database = await self.get_database(ctx=ctx)
        if not database.export_user_queue_to_csv(f"{ctx.guild.id}_user_queue.csv"):
            await self.send_error(ctx=ctx)
            return
        await ctx.send(file=discord.File(f"{ctx.guild.id}_user_queue.csv"))

    @queue.group(name="items")
    async def queue_items(self, ctx: Context):
        pass

    @queue_items.command(name="new")
    async def queue_items_new(self, ctx: Context, queue_name: str):
        """
        Creates a new items queue
        """
        await self.create_new_queue(ctx=ctx, queue_name=queue_name, queue_type=QueueType.ITEMS)
