import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from peaqevcore.models.hub.const import CHARGERDONE

from .const import (
    DOMAIN)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):  # pylint:disable=unused-argument
    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = []

    peaqsensors.append(PeaqBinarySensorDone(hub))
    async_add_entities(peaqsensors)

SCAN_INTERVAL = timedelta(seconds=4)


class PeaqBinarySensorDone(BinarySensorEntity):
    def __init__(self, hub) -> None:
        """Initialize a Peaq Binary sensor."""
        self._attr_name = f"{hub.hubname} {CHARGERDONE}"
        self._hub = hub
        self._attr_device_class = "none"

    @property
    def unique_id(self):
        return f"{DOMAIN.lower()}_{self._attr_name}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}

    @property
    def is_on(self) -> bool:
        try:
            return self._hub.sensors.charger_done.value
        except:
            _LOGGER.debug("Binarysensor_charger_done could not get state from hub.")
            return False
