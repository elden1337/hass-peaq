from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub import HomeAssistantHub

_LOGGER = logging.getLogger(__name__)


class MaxMinController:
    def __init__(self, hub: HomeAssistantHub):
        self.hub = hub
        self._override_max_charge = None
        self._original_total_charge = 0
        self.override_max_charge: bool = False
        self.hub.observer.add("car disconnected", self.async_null_max_charge, _async=True)
        self.hub.observer.add("car done", self.async_null_max_charge, _async=True)
        self.hub.observer.add(
            "update charger enabled", self.async_null_max_charge, _async=True
        )

    @property
    def max_charge(self) -> int:
        if self._override_max_charge is not None:
            """overridden by frontend"""
            return self._override_max_charge
        if self.hub.options.max_charge > 0:
            """set in config flow"""
            return self.hub.options.max_charge
        return self._original_total_charge

    async def async_override_max_charge(self, max_charge: int):
        """Overrides the max-charge with the input from frontend"""
        if self.hub.options.price.price_aware:
            self._override_max_charge = max_charge
            await self.hub.hours.async_update_max_min(self.max_charge)

    async def async_null_max_charge(self, val=None):
        """Resets the max-charge to the static value, listens to charger done and charger disconnected"""
        if val is None:
            self._override_max_charge = None
        elif val is False:
            self._override_max_charge = None
        if self._override_max_charge is None:
            await self.async_reset_max_charge_sensor()

    async def async_reset_max_charge_sensor(self) -> None:
        try:
            state = self.hub.state_machine.states.get("number.peaqev_max_charge")
            if state is not None:
                if state == self.max_charge or self.max_charge == 0:
                    return
            await self.hub.state_machine.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": "number.peaqev_max_charge",
                    "value":     int(self.max_charge),
                },
            )
            _LOGGER.debug(
                f"Resetting max charge to static value {int(self.max_charge)}"
            )
        except Exception as e:
            _LOGGER.error(f"Encountered problem when trying to reset max charge to normal: {e}")
            return
