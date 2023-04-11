from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MAX_CHARGE = "Max Charge"


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities
):  # pylint:disable=unused-argument
    hub = hass.data[DOMAIN]["hub"]

    inputnumbers = [{"name": MAX_CHARGE, "entity": "_max_charge"}]

    async_add_entities(PeaqNumber(i, hub) for i in inputnumbers)


class PeaqNumber(NumberEntity, RestoreEntity):
    def __init__(self, number, hub) -> None:
        self._number = number
        self._attr_name = f"{hub.hubname} {self._number['name']}"
        self._hub = hub
        self._attr_device_class = None
        self._state = None

    @property
    def native_max_value(self) -> float:
        return 100

    @property
    def native_min_value(self) -> float:
        return 0

    @property
    def native_step(self) -> float:
        return 1

    @property
    def native_value(self) -> float | None:
        return self._state

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "kWh"

    @property
    def mode(self) -> str:
        return "auto"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._hub.hubname}_{self._number['entity']}"

    async def async_set_native_value(self, value: float) -> None:
        self._state = value
        await self.hub.async_update_charge_limit(int(value))

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            await self.async_set_native_value(float(state.state))
        else:
            await self.async_set_native_value(100)
