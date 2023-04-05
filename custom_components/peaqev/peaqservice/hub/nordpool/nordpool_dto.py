import logging
from dataclasses import dataclass, field

_LOGGER = logging.getLogger(__name__)


@dataclass
class NordpoolDTO:
    state: float = 0
    today: list = field(default_factory=lambda: [])
    tomorrow: list = field(default_factory=lambda: [])
    average: float = 0
    currency: str = ""
    price_in_cent: bool = False

    async def set_model(self, ret):
        try:
            self.today = list(ret.attributes.get("today"))
        except Exception as e:
            _LOGGER.exception(
                f"Could not parse today's prices from Nordpool. Unsolveable error. {e}"
            )
            return
        self.tomorrow = list(ret.attributes.get("tomorrow", []))
        self.currency = str(ret.attributes.get("currency", ""))
        self.state = ret.state
        self.average = float(str(ret.attributes.get("average", 0)))
        self.price_in_cent = bool(ret.attributes.get("price_in_cent", False))
