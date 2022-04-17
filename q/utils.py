import enum
from typing import Union, Type

import discord

from q.database import UserQueueEntry, ItemQueueEntry, QueueEntry


class QueueType(enum.Enum):
    USERS = 1,
    ITEMS = 1,

    @classmethod
    def from_string(cls, string: str) -> Union['QueueType', None]:
        if string == 'users':
            return QueueType.USERS
        elif string == 'items':
            return QueueType.ITEMS
        else:
            return None

    @property
    def string(self) -> str:
        return self.name.lower()

    @property
    def schema(self) -> Type[QueueEntry]:
        if self == QueueType.USERS:
            return UserQueueEntry
        elif self == QueueType.ITEMS:
            return ItemQueueEntry
        else:
            raise ValueError(f'Invalid queue type: {self}')


def int_to_place(n: int) -> str:
    """
    Convert a number to a place.
    """
    last_digit = int(repr(n)[-1])
    last_two_digits = int(repr(n)[-2:])
    suffix = 'th'
    if last_digit == 1 and last_two_digits != 11:
        suffix = 'st'
    elif last_digit == 2 and last_two_digits != 12:
        suffix = 'nd'
    elif last_digit == 3 and last_two_digits != 13:
        suffix = 'rd'
    return f"{n}{suffix}"


def get_guild_database(guild: discord.Guild) -> str:
    """
    Get the database name for a guild.
    """
    return f"{guild.id}_queue.db"
