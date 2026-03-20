from enum import Enum, unique

from pydantic import BaseModel


@unique
class RateLimitType(Enum):
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"

    @property
    def rate_limit_milliseconds(self) -> int:
        """Returns the corresponding rate limit in milliseconds."""
        rate_limits = {
            RateLimitType.MINUTE: 60 * 1000,
            RateLimitType.HOUR: 60 * 60 * 1000,
            RateLimitType.DAY: 24 * 60 * 60 * 1000,
            RateLimitType.WEEK: 7 * 24 * 60 * 60 * 1000,
            RateLimitType.MONTH: 30 * 24 * 60 * 60 * 1000,
            RateLimitType.YEAR: 365 * 24 * 60 * 60 * 1000,
        }

        return rate_limits.get(self, 0)


class EncryptAPIKey(BaseModel):
    name: str
    encrypted_api_key: bytes
    rate_limit: int
    rate_limit_type: RateLimitType
