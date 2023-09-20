import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

_LOGGER = logging.getLogger(__name__)


@dataclass
class SpotPriceModel:
    source: str
    currency: str = ""
    prices: list = field(default_factory=lambda: [])
    prices_tomorrow: list = field(default_factory=lambda: [])
    state: float = 0
    entity: str = ""
    average_data: dict = field(default_factory=lambda: {})
    average_month: float = 0
    adjusted_average: float = 0
    average_weekly: float = 0
    average_three_days: float = 0
    average_30: float = 0
    tomorrow_valid: bool = False
    daily_average: float = 0
    use_cent: bool = False
    dynamic_top_price_type: str = ""
    dynamic_top_price: float|None = None

    def create_date_dict(self, numbers: dict|list) -> None:
        if isinstance(numbers, dict):
            try:
                ret = {datetime.strptime(key, "%Y-%m-%d").date(): value for key, value in numbers.items()}
            except ValueError:
                _LOGGER.error("Could not convert date string to date object")
                ret = {}
        else:
            today = date.today()
            delta = timedelta(days=len(numbers) - 1)
            start_date = today - delta
            ret = {}
            for number in numbers:
                ret[start_date] = number
                start_date += timedelta(days=1)
        self.average_data = ret

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
