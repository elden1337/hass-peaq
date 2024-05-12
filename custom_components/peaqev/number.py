from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

import logging

from homeassistant.components.number import NumberEntity  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers.restore_state import RestoreEntity  # type: ignore
from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MAX_CHARGE = 'Max Charge'


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities
):  # pylint:disable=unused-argument
    hub: HomeAssistantHub = hass.data[DOMAIN]['hub']

    entities = []
    inputnumbers = [{'name': MAX_CHARGE, 'entity': '_max_charge'}]
    if hub.options.price.price_aware and not hub.options.peaqev_lite:
        entities.extend(PeaqNumber(i, hub) for i in inputnumbers)
        entities.append(PeaqMaxMinLimiterNumber('Max min limiter', hub))
        async_add_entities(entities)


class PeaqMaxMinLimiterNumber(NumberEntity, RestoreEntity):
    """If max-min is used, this value can be set to ignore maxmin if the per-kwh-cost of maxmin vs regular is less than this value."""
    def __init__(self, name, hub) -> None:
        self._number = name
        self.hub = hub
        self._currency = self.hub.spotprice.currency
        # self._use_cent = self.hub.spotprice.use_cent
        # self._multiplier = 100 if self._use_cent else 1
        self._attr_name = f'{hub.hubname} {self._number}'

        self._attr_device_class = None
        self._state = None

    @property
    def multiplier(self) -> int:
        return 100 if self.hub.spotprice.use_cent else 1

    @property
    def native_max_value(self) -> float:
        return 1 * self.multiplier

    @property
    def native_min_value(self) -> float:
        return 0

    @property
    def native_step(self) -> float:
        return 0.05 * self.multiplier

    @property
    def native_value(self) -> float | None:
        return self._state

    @property
    def native_unit_of_measurement(self) -> str | None:
        return f'{self.hub.spotprice.currency}/kWh'

    @property
    def mode(self) -> str:
        return 'box'

    @property
    def icon(self) -> str:
        return 'mdi:adjust'

    @property
    def unique_id(self) -> str:
        return f'{DOMAIN}_{self.hub.hubname}_{self._number}'

    async def async_set_native_value(self, value: float) -> None:
        self._state = value
        self.hub.max_min_controller.max_min_limiter = value

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            if state.state != self._state:
                _LOGGER.debug(
                    f'Restoring state {state.state} for {self.name}.'
                )
                await self.async_set_native_value(float(state.state))
            else:
                self._state = 0
        else:
            self._state = 0

class PeaqNumber(NumberEntity, RestoreEntity):
    """Sensor to override the set max-min charge level."""
    def __init__(self, number, hub) -> None:
        self._number = number
        self._attr_name = f"{hub.hubname} {self._number['name']}"
        self.hub = hub
        self._attr_device_class = None
        self._state = None

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
        return 'kWh'

    @property
    def mode(self) -> str:
        return 'slider'

    @property
    def icon(self) -> str:
        return 'mdi:adjust'

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.hub.hubname}_{self._number['entity']}"

    async def async_set_native_value(self, value: float) -> None:
        if (
            int(value) != self.hub.max_min_controller.max_charge
            and self.hub.max_min_controller.max_charge > 0
        ):
            """Overriding default"""
            await self.hub.max_min_controller.async_override_max_charge(int(value))
            self.hub.max_min_controller.override_max_charge = True
            self._state = value
        else:
            self.hub.max_min_controller.override_max_charge = False
            self._state = int(self.hub.max_min_controller.max_charge)

    async def async_added_to_hass(self):
        _set_max = self.hub.max_min_controller.max_charge
        if not self.hub.enabled or self.hub.chargecontroller.status_type in [
            ChargeControllerStates.Done,
            ChargeControllerStates.Idle,
            ChargeControllerStates.Disabled,
        ]:
            self._state = _set_max
            self.hub.max_min_controller.override_max_charge = False
        else:
            state = await super().async_get_last_state()
            if state:
                if state.state != _set_max:
                    _LOGGER.debug(
                        f'Restoring state {state.state} for {self.name}. hub reports: {_set_max}'
                    )
                    await self.async_set_native_value(float(state.state))
                else:
                    self._state = _set_max
            else:
                self._state = _set_max
