from dataclasses import dataclass, field
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class NordpoolDTO:
    state: float = field(init=False)
    today: list = field(init=False)
    tomorrow: list = field(init=False)
    average: float = field(init=False)
    currency: str = field(init=False)
    
    async def set_model(self, ret):
        try:
            self.today = list(ret.attributes.get("today"))
        except Exception as e:
            _LOGGER.exception(f"Could not parse today's prices from Nordpool. Unsolveable error. {e}")
            return
        self.tomorrow = list(ret.attributes.get("tomorrow"), [])
        self.currency = str(ret.attributes.get("currency"), "")
        self.state = ret.state
        self.average = float(str(ret.attributes.get("average")), 0)