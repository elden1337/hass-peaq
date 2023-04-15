from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from peaqevcore.models.hub.const import CHARGERDONE

from custom_components.peaqev.const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PeaqBinarySensorDone(BinarySensorEntity):
    def __init__(self, hub: HomeAssistantHub) -> None:
        """Initialize a Peaq Binary sensor."""
        self._attr_name = f"{hub.hubname} {CHARGERDONE}"
        self.hub = hub
        self._attr_device_class = "none"

    @property
    def unique_id(self):
        return f"{DOMAIN.lower()}_{self._attr_name}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.hub.hub_id)}}

    @property
    def is_on(self) -> bool:
        if self.hub.is_initialized:
            try:
                return self.hub.charger_done
            except:
                _LOGGER.debug("Binarysensor_charger_done could not get state from hub.")
                return False
        return False
