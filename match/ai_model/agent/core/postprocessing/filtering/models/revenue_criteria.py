from pydantic import BaseModel


class RevenueCriteria(BaseModel):
    min_revenue: float = 5e6
    max_consider_days: int = 60
    period_in_day: int = 30
