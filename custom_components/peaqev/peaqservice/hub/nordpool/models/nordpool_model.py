from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class NordPoolModel:
    currency: str = ""
    prices: list = field(default_factory=lambda: [])
    prices_tomorrow: list = field(default_factory=lambda: [])
    state: float = 0
    nordpool_entity: str = ""
    average_data: dict = field(default_factory=lambda: {})
    average_month: float = 0
    average_weekly: float = 0
    average_three_days: float = 0
    average_30: float = 0
    daily_average: float = 0
    use_cent: bool = False
    dynamic_top_price_type: str = ""
    dynamic_top_price: float|None = None

    async def async_create_date_dict(self, numbers: dict[date,float]|list[float]) -> dict[date, float]:
        if isinstance(numbers, dict):
            return numbers
        today = date.today()
        delta = timedelta(days=len(numbers) - 1)
        start_date = today - delta
        ret = {}
        for number in numbers:
            ret[start_date] = number
            start_date += timedelta(days=1)
        return ret

    async def fix_dst(self, val) -> list | None:
        if val is None:
            return None
        if len(val) < 1:
            return []
        ll = [h for h in val if h is not None]
        av = round(min(ll), 3)
        if len(val) == 23:
            val.insert(2, av)
        elif val[2] is None:
            val[2] = av
        return val
