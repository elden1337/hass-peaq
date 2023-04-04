from dataclasses import dataclass, field
from typing import List

@dataclass
class Price:
    price_aware: bool = False
    min_price: float = 0.0
    top_price: float = 0.0
    cautionhour_type: str = ""
    dynamic_top_price: bool = False

@dataclass
class Charger:
    chargertype: str = ""
    chargerid: str = ""
    powerswitch: str = ""
    powermeter: str = ""

@dataclass
class HubOptions:
    locale: str = field(init=False)
    charger: Charger = Charger()
    price: Price = Price()
    peaqev_lite: bool = False
    powersensor_includes_car: bool = False
    powersensor: str = field(init=False)
    startpeaks: dict = field(default_factory=dict)
    cautionhours: List = field(default_factory=lambda: [])
    nonhours: List = field(default_factory=lambda: [])
    fuse_type: str = ""
    blocknocturnal: bool = False
    gainloss: bool = False
    """blocks charging during the night for safety concern reasons."""

