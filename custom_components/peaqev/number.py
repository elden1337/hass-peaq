from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers.restore_state import RestoreEntity  # type: ignore

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MAX_CHARGE = "Max Charge"


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities
):  # pylint:disable=unused-argument
    hub = hass.data[DOMAIN]["hub"]

    inputnumbers = [{"name": MAX_CHARGE, "entity": "_max_charge"}]
    if hub.options.price.price_aware:
        async_add_entities(PeaqNumber(i, hub) for i in inputnumbers)


class PeaqNumber(NumberEntity, RestoreEntity):
    def __init__(self, number, hub) -> None:
        self._number = number
        self._attr_name = f"{hub.hubname} {self._number['name']}"
        self.hub = hub
        self._attr_device_class = None
        self._state = None
        self._icon = "mdi:image-auto-adjust"

    @property
    def native_max_value(self) -> float:
        return 70

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
        return "slider"

    @property
    def icon(self) -> str:
        return self._icon

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.hub.hubname}_{self._number['entity']}"

    async def async_set_native_value(self, value: float) -> None:
        if int(value) != self.hub.max_charge and self.hub.max_charge > 0:
            """Overriding default"""
            await self.hub.async_override_max_charge(int(value))
            self._icon = "mdi:adjust"
            self.hub.override_max_charge = True
            self._state = value
        else:
            self._icon = "mdi:image-auto-adjust"
            self.hub.override_max_charge = False
            self._state = int(self.hub.max_charge)

    async def async_added_to_hass(self):
        # if the state is different from hub.max_charge
        # do stuff

        state = await super().async_get_last_state()
        if state:
            if state.state != self.hub.max_charge:
                _LOGGER.debug(
                    f"Restoring state {state.state} for {self.name}. hub reports: {self.hub.max_charge}"
                )
                await self.async_set_native_value(float(state.state))
            else:
                self._state = self.hub.max_charge
        else:
            self._state = self.hub.max_charge
