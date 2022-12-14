from enum import Enum


class ChainSyncStatus(float, Enum):
    UNKNOWN = -1
    SYNCING = 0
    SYNCED = 1
    STOPPED = -1.1
