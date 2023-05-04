from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.sensors.money_sensor_helpers import (
    async_currency_translation,
)
from custom_components.peaqev.sensors.sensorbase import SensorBase

_LOGGER = logging.getLogger(__name__)


class PeaqSavingsSensor(SensorBase, RestoreEntity):
    device_class = SensorDeviceClass.MONETARY

    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f"{hub.hubname} savings"
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._listen_status = None
        self._currency = None
        self._state: float = 0
        self._savings_peak = None
        self._savings_trade = None
        self._data_dump = None

    @property
    def state(self) -> float:
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
            "savings_total",
            "export_savings_data",
        )

        if ret is not None:
            self._currency = ret.get("currency")
            self._listen_status = self.hub.chargecontroller.savings.status.value
            self._data_dump = ret.get("export_savings_data")
            self._savings_peak = await async_currency_translation(
                value=ret.get("savings_peak", 0),
                currency=ret.get("currency"),
                use_cent=ret.get("use_cent", False),
            )
            self._savings_trade = await async_currency_translation(
                value=ret.get("savings_trade", 0),
                currency=ret.get("currency"),
                use_cent=ret.get("use_cent", False),
            )
            if self.hub.options.price.price_aware:
                self._state = ret.get("savings_total", 0)
            else:
                self._state = ret.get("savings_peak", 0)
        if self._state > 0:
            _LOGGER.debug("savings have been registered. resetting savingsservice")
            await self.hub.chargecontroller.savings.service.async_stop_listen()

    @property
    def extra_state_attributes(self) -> dict:
        # todo: fix attr for persisting the consumption-dict and connected-at
        attr_dict = {
            "Savings peak": self._savings_peak,
            "Listen status": self._listen_status,
        }
        if self.hub.options.price.price_aware:
            attr_dict["Savings trade"] = self._savings_trade
        attr_dict["Data"] = self._data_dump
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        _LOGGER.debug("last state of %s = %s", self._attr_name, state)
        if state:
            self._data_dump = state.attributes.get("Data")
            self._savings_peak = state.attributes.get("Savings peak")
            self._savings_trade = state.attributes.get("Savings trade")
            self._state = state.state
            await self.hub.chargecontroller.savings.async_import_data(self._data_dump)
        else:
            pass
