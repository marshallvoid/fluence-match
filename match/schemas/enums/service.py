from enum import StrEnum, unique
from typing import Set


@unique
class ServiceSessionStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

    @classmethod
    def finished_statuses(cls) -> Set["ServiceSessionStatus"]:
        return {cls.COMPLETED, cls.CANCELLED, cls.FAILED}
