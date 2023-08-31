import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from statistics import mean

_LOGGER = logging.getLogger(__name__)


@dataclass
class ISpotPriceDTO:
    state: float = 0
    today: list = field(default_factory=lambda: [])
    tomorrow: list = field(default_factory=lambda: [])
    average: float = 0
    currency: str = ""
    price_in_cent: bool = False #todo: add support when source exposes this option.
    tomorrow_valid: bool = False

    async def set_model(self, ret):
        try:
            self.today = list(ret.attributes.get("today"))
        except Exception as e:
            _LOGGER.exception(
                f"Could not parse today's prices. Unsolveable error. {e}"
            )
            return
        self.tomorrow_valid = bool(ret.attributes.get("tomorrow_valid", False))
        _tomorrow = ret.attributes.get("tomorrow", [])
        if _tomorrow is not None:
            self.tomorrow = list(_tomorrow)
        else:
            self.tomorrow = []
        self.currency = str(ret.attributes.get("currency", ""))
        self.state = ret.state
        self.average = self._set_average(ret)
        self.price_in_cent = self._set_price_in_cent(ret)

    @abstractmethod
    def _set_price_in_cent(self, ret) -> bool:
        pass

    @abstractmethod
    def _set_average(self, ret) -> float:
        pass


@dataclass
class EnergiDataServiceDTO(ISpotPriceDTO):

    def _set_price_in_cent(self, ret) -> bool:
            return bool(ret.attributes.get("use_cent", False))

    def _set_average(self, ret) -> float:
        try:
            return round(mean(self.today), 2)
        except Exception as e:
            _LOGGER.exception(
                f"Could not parse today's prices from EnergiDataService. Unsolveable error. {e}"
            )
            return 0



@dataclass
class NordpoolDTO(ISpotPriceDTO):
    
    def _set_price_in_cent(self, ret) -> bool:
        return bool(ret.attributes.get("price_in_cent", False))

    def _set_average(self, ret) -> float:
        try:
            return float(str(ret.attributes.get("average", 0)))
        except Exception as e:
            _LOGGER.exception(
                f"Could not parse today's prices from Nordpool. Unsolveable error. {e}"
            )
            return 0