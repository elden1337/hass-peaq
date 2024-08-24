from dataclasses import dataclass, field
from typing import List

from peaqevcore.common.spotprice.models.spotprice_type import SpotPriceType

from custom_components.peaqev.peaqservice.util.options_comparer import OptionsComparer


@dataclass
class Price(OptionsComparer):
    price_aware: bool = False
    min_price: float = 0.0
    top_price: float = 0.0
    cautionhour_type: str = ''
    dynamic_top_price: bool = False
    custom_sensor: str = None
    spotprice_type: SpotPriceType = SpotPriceType.Auto


@dataclass
class Charger(OptionsComparer):
    chargertype: str = ''
    chargerid: str = ''
    powerswitch: str = ''
    powermeter: str = ''


@dataclass
class HubOptions:
    locale: str = field(init=False)
    charger: Charger = field(init=False)
    price: Price = field(init=False)
    peaqev_lite: bool = False
    powersensor_includes_car: bool = False
    powersensor: str = field(init=False)
    _startpeaks: dict = field(default_factory=dict)
    cautionhours: List = field(default_factory=lambda: [])
    nonhours: List = field(default_factory=lambda: [])
    fuse_type: str = ''
    gainloss: bool = False
    max_charge: int = 0
    use_peak_history: bool = False

    def __post_init__(self):
        self.charger = Charger()
        self.price = Price()

    @property
    def startpeaks(self):
        return self._startpeaks
    @startpeaks.setter
    def startpeaks(self, value):
        self._startpeaks = {int(k): v for k, v in value.items()}

    def compare(self, other) -> list:
        diff = []
        for key, value in self.__dict__.items():
            if key not in other.__dict__.keys():
                diff.append(key)
            elif key in ['charger', 'price']:
                diff.extend(value.compare(other=other.__dict__[key]))
            elif value != other.__dict__[key]:
                diff.append(key)
        return diff
