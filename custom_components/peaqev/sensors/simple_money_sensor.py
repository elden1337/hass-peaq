from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from custom_components.peaqev.sensors.money_sensor_helpers import *
from custom_components.peaqev.sensors.sensorbase import MoneyDevice

_LOGGER = logging.getLogger(__name__)


class PeaqSimpleMoneySensor(MoneyDevice):
    def __init__(self, hub: HomeAssistantHub, entry_id, sensor_name: str, caller_attribute: str):
        name = f"{hub.hubname} {sensor_name}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None
        self._caller_attribute = caller_attribute
        self._use_cent = None
        self._currency = None

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:car-clock"

    async def async_update(self) -> None:
        self._use_cent = self.hub.spotprice.use_cent
        self._currency = self.hub.spotprice.currency
        ret = getattr(self.hub.spotprice, self._caller_attribute)
        if ret is not None:
            self._state = currency_translation(ret, self._currency, self._use_cent)

