from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity  # type: ignore

from custom_components.peaqev import DOMAIN
from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities
):  # pylint:disable=unused-argument
    hub: HomeAssistantHub = hass.data[DOMAIN]['hub']

    entities = []
    if hub.options.price.price_aware and not hub.options.peaqev_lite:
        entities.append(PeaqSelectEntity('Scheduler next departure', hub.scheduler_options_handler))
        async_add_entities(entities)


class PeaqSelectEntity(SelectEntity, RestoreEntity):
    def __init__(self, name, options_handler):
        self._attr_name = name
        self.scheduler = options_handler
        self._attr_options = self.scheduler.display_options
        self._attr_current_option = None

    async def async_update(self):
        self._attr_options = self.scheduler.display_options
        self._attr_current_option = self.scheduler.current_option
        if self._attr_current_option not in self._attr_options:
            self._attr_current_option = self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug('Selected option: %s', option)
        await self.scheduler.async_handle_scheduler_departure_option(option)
        self._attr_current_option = option

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        if state:
            if state.state != self._attr_current_option:
                _LOGGER.debug(
                    f'Restoring state {state.state} for {self.name}.'
                )
                await self.async_select_option(state.state)
            else:
                self._attr_current_option = self._attr_options[0]
        else:
            self._attr_current_option = self._attr_options[0]
