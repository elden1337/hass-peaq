from dataclasses import dataclass, field

@dataclass
class NordPoolModel:
    currency: str = ""
    prices: list = field(default_factory=lambda: [])
    prices_tomorrow: list = field(default_factory=lambda: [])
    state: float = 0
    nordpool_entity: str = ""
    average_data: list = field(default_factory=lambda: [])
    average_month: float = 0
    average_weekly: float = 0
    daily_average: float = 0
