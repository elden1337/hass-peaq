from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

import logging

from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.peaqservice.util.constants import HOURCONTROLLER
from custom_components.peaqev.sensors.money_sensor_helpers import \
    async_currency_translation
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


class PeaqMoneySensor(SensorBase, RestoreEntity):
    """Special sensor which is only created if priceaware is true"""

    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} {HOURCONTROLLER}"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._currency = None
        self._state = None
        self._savings_peak = None
        self._savings_trade = None

    @property
    def state(self):
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:cash-refund"

    async def async_update(self) -> None:
        ret = await self.hub.async_request_sensor_data(
            "currency",
            "use_cent",
            "savings_peak",
            "savings_trade",
            "savings_total"
        )
        if ret is not None:
            self._currency = ret.get("currency")
            self._savings_peak = await async_currency_translation(
                value=ret.get("savings_peak"),
                currency=ret.get("currency"),
                use_cent=ret.get("use_cent", False),
            )
            self._savings_trade = await async_currency_translation(
                value=ret.get("savings_trade"),
                currency=ret.get("currency"),
                use_cent=ret.get("use_cent", False),
            )
            if self.hub.options.price.price_aware:
                self._state = await async_currency_translation(
                value=ret.get("savings_total"),
                currency=ret.get("currency"),
                use_cent=ret.get("use_cent", False),
            )
            else:
                self._state = self._savings_peak


    @property
    def extra_state_attributes(self) -> dict:
        #todo: fix attr for persisting the consumption-dict and connected-at
        attr_dict = {
            "Savings peak": self._savings_peak
        }
        if self.hub.options.price.price_aware:
            attr_dict["Savings trade"] = self._savings_trade

        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        _LOGGER.debug("last state of %s = %s", self._attr_name, state)
        if state:
            pass
            #todo add restore state
        else:
            pass
            # todo add restore state

