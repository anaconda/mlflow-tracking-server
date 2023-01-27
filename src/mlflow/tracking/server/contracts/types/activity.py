""" Defines acceptable project launch types """

from enum import Enum


class ActivityType(str, Enum):
    """Type of activity to occur"""

    SERVER = "server"
    GC = "gc"
    DB_UPGRADE = "db_upgrade"
