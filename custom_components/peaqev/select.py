from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity

_LOGGER = logging.getLogger(__name__)


# async def async_setup_entry(
#     hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
# ) -> None:
#     """Set up the sensors."""
#
#     coordinator = hass.data[DOMAIN][entry.entry_id]
#     entities: list[SelectEntity] = []
#
#     for system in coordinator.data:
#         for device in system.devices:
#             for parameter in device.parameters:
#                 if parameter.find_fitting_entity() == Platform.SELECT:
#                     entities.append(
#                         MyUplinkParameterSelectEntity(coordinator, device, parameter)
#                     )
#
#     async_add_entities(entities)


class MyUplinkParameterSelectEntity(SelectEntity):
    def __init__(self, hub):
        self.hub = hub
        self._attr_options = self.hub.scheduler_options_handler.display_options
        self._attr_current_option = self._attr_options[0]

    def async_update(self):
        self._attr_options = self.hub.scheduler_options_handler.display_options

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.hub.scheduler_options_handler.async_handle_scheduler_departure_option(option)
        self._attr_current_option = option
