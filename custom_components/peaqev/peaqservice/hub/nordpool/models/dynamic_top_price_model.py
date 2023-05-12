from dataclasses import dataclass, field


@dataclass
class DynamicTopPriceModel:
    three: list = field(default_factory=lambda: [])
    seven: list = field(default_factory=lambda: [])
    thirty: list = field(default_factory=lambda: [])
    month: list = field(default_factory=lambda: [])
